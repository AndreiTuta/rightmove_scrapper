# auth.py
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import datetime


class SpreadHandler():
    
    def __init__(self, spreadsheet_key: str):
        gc = gspread.service_account(filename='credentials.json')

        self.gsheet = gc.open_by_key(spreadsheet_key)
        

    def write(self, title, data, headers):
        for region, locations in data.items():
            new_row_index = 1
            wsheet = self.gsheet.add_worksheet(f'{title}- {region}', 200, 32)
            wsheet.insert_row(headers, new_row_index)
            for name, location in locations.items():
                for price, prop in location.items():
                    print(f'{price}: {prop}')
                    new_row_index +=1
                    info = [price, prop.title, prop.monthly_payment, prop.map_location, prop.added, prop.prop_type, prop.bedrooms, prop.bathrooms]
                    wsheet.insert_row(info, new_row_index)