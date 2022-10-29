def read_csv_to_list(service, spread_sheet_id, data_range):

    # Call the Sheets API
    sheet = service.spreadsheets()
    google_sheet = sheet.values().get(spreadsheetId=spread_sheet_id,
                                range=data_range).execute()
    rows = google_sheet.get('values', [])

    return rows


def write_to_csv(data, service, spreadsheet_id, spreadsheet_range):
    sheet = service.spreadsheets()
    sheet.values().update(
        spreadsheetId=spreadsheet_id, range=spreadsheet_range,
        valueInputOption='RAW', body={"values": data}).execute()

def delete_portion_csv(service, spreadsheet_id, spreadsheet_range):
    sheet = service.spreadsheets()
    sheet.values().clear(
        spreadsheetId=spreadsheet_id, range=spreadsheet_range).execute()

