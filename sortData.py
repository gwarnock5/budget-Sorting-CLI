import json
import sys
from googleapiclient.discovery import build
from google.oauth2 import service_account
import googlesheets
import localcsv
from datetime import datetime


def convert_row(row):
    statement = row[1].lower()
    deposit = row[2]
    expense = row[3] if len(row) > 3 else ''
    if deposit != '':
        deposit = deposit.replace('$', '')
        deposit = deposit.replace(',', '')
        deposit = float(deposit)
    if expense != '':
        expense = expense.replace('$', '')
        expense = expense.replace(',', '')
        expense = float(expense)

    return [statement, deposit, expense]

 
def convert_data(data):
    extracted_data = []
    # extracting each data row one by one
    for row in data:
        row_converted_data = convert_row(row)
        extracted_data.append(row_converted_data)

    return extracted_data
    

def read_json_to_dict(file_path):

    with open(file_path, 'r') as f:
        data = json.load(f)

    return data


def construct_key_words_dict(file_path):
    key_words = read_json_to_dict(file_path)

    for key, value in key_words.items():
        key_words[key] = read_json_to_dict('./categoriesData/' + value)

    return key_words


def find_category(row, key_words):
    category = False
    for key, value in key_words.items():
        for key2 in value:
            if key2 in row[0]:
                category = key

    return category


def sort_data(current_data):
    key_words = construct_key_words_dict('./keyWords.json')
    results = {}
    failures = []

    results['Income'] = []
    for key in key_words:
        results[key] = []

    for data_row in current_data:
        print(data_row)
        category = find_category(data_row, key_words)
        if data_row[1] != '':
            results['Income'].append(data_row[1])
        elif category:
            results[category].append(data_row[2])
        else:
            failures.append(data_row)

    return dict_to_list(results), failures


def dict_to_list(dict):
    results_list = []
    for key, value in dict.items():
        value.insert(0,key)
        results_list.append(value)

    return results_list


def main(location, month=None):

    if location == "local":
        current_data = localcsv.read_csv_to_list()
        formatted_data = convert_data(current_data)
        results, failures = sort_data(formatted_data)
        localcsv.write_to_csv(results, 'results')
        localcsv.write_to_csv(failures, 'failures')
    elif location == "google":
        SERVICE_ACCOUNT_FILE = '../apiKeys/serviceaccount-key.json'
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        credentials = None
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)

        spread_sheet_ids = read_json_to_dict('../apiKeys/budgetSpreadSheetIds.json')

        temp_data_range = 'tempData!A1:L50'
        results_data_range = 'results!A1:L20'
        failures_data_range = 'failures!A1:L20'


        current_data = googlesheets.read_csv_to_list(service, spread_sheet_ids["temp_data_spreadsheet_id"], 
                                                     temp_data_range)
        formatted_data = convert_data(current_data)
        results, failures = sort_data(formatted_data)

        googlesheets.delete_portion_csv(service, spread_sheet_ids["results_spreadsheet_id"], results_data_range)
        googlesheets.write_to_csv(results, service, spread_sheet_ids["results_spreadsheet_id"], results_data_range)
        googlesheets.delete_portion_csv(service, spread_sheet_ids["failures_spreadsheet_id"], failures_data_range)
        googlesheets.write_to_csv(failures, service, spread_sheet_ids["failures_spreadsheet_id"], failures_data_range)
    elif location == "move":
        if not month:
            month = datetime.now().strftime('%B')

        SERVICE_ACCOUNT_FILE = '../apiKeys/serviceaccount-key.json'
        SCOPES = ['https://www.googleapis.com/auth/spreadsheets']

        credentials = None
        credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
        service = build('sheets', 'v4', credentials=credentials)

        spread_sheet_ids = read_json_to_dict('../apiKeys/budgetSpreadSheetIds.json')

        results_data_range = 'results!A1:L20'
        results_data = googlesheets.read_csv_to_list(service, spread_sheet_ids['results_spreadsheet_id'],
                                                     results_data_range)

        monthly_read_data_range = f"{month}!A1:R20"
        budget_data = googlesheets.read_csv_to_list(service, spread_sheet_ids['budget_spreadsheet_id'],
                                                    monthly_read_data_range)


        string_data_to_write = []
        for i in range(20):
            temp_list = []
            if budget_data[i][0] == '':
                continue
            elif budget_data[i][0].strip() == results_data[i-1][0].strip():
                if len(results_data[i-1]) > 1:
                    column_to_begin_writing = len(budget_data[i]) + 1
                    column_letter_start = chr(ord('@') + column_to_begin_writing)
                    column_to_end_writing = len(budget_data[i]) + len(results_data[i-1])
                    column_letter_end = chr(ord('@') + column_to_end_writing)

                    temp_list.extend(results_data[i-1][1:])
                    string_data_to_write.append({"results": temp_list, 
                                                 "data_range": f"{month}!{column_letter_start}{i+1}:{column_letter_end}{i+1}", 
                                                 "category_name": results_data[i-1][0]})
            else:
                raise Exception(f"All column names should match. Budget: '{budget_data[i][0]}' - Results: '{results_data[i-1][0]}'")
        
        float_data_to_write = []
        for data in string_data_to_write:
            float_data_to_write.append({"results": [[float(i) for i in data["results"]]], 
                                        "data_range": data["data_range"], 
                                        "category_name": data["category_name"]})


        for i in range(len(float_data_to_write)):
            print(f"{float_data_to_write[i]['category_name']} - {float_data_to_write[i]['results'][0]}")
        

        user_response = input(f"The above data will be written to the {month} sheet, Are you positive this is correct? ")
        if user_response.lower() != "y":
            print("Process ended before submitting data.")
            return
        # Add a confirmation here that will double check I want to move the data.
        for i in range(len(float_data_to_write)):
            if float_data_to_write[i]["results"] != [[]] and float_data_to_write[i]["data_range"] != '':
                print(f"{float_data_to_write[i]['category_name']}: {float_data_to_write[i]['results'][0]} - {float_data_to_write[i]['data_range']}")
                googlesheets.write_to_csv(float_data_to_write[i]['results'], service, spread_sheet_ids['budget_spreadsheet_id'], 
                                          float_data_to_write[i]['data_range'])


if __name__ == '__main__':
    if len(sys.argv) > 1:
        if sys.argv[1] == '-l':
            location = 'local'
        elif sys.argv[1] == '-g':
            location = 'google'
        elif sys.argv[1] == '-m':
            # TODO: Implement ability to pass in month...
            location = 'move'
        # -u will remove matching amounts starting at the end of each row. Has to be the end of the row.
        else:
            location = None
         
        if location == 'google' or location == 'local' or location == 'move':
            main(location)

