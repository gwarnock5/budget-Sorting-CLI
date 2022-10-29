import csv

def read_csv_to_list():
    file_path = './tempData.csv'
    rows = []
    with open(file_path, 'r') as csvfile:
        # creating a csv reader object
        csvreader = csv.reader(csvfile)
        for row in csvreader:
            rows.append(row)

    return rows


def write_to_csv(data, file_type):
    if file_type == 'results':
        file_path = './results.csv'
    elif file_type == 'failures':
        file_path = './failures.csv'


    with open(file_path, 'w', newline='') as csvfile: 
        csvwriter = csv.writer(csvfile) 
        csvwriter.writerows(data)