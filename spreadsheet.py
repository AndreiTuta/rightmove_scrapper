import gspread as gspread

import logging

logger = logging.getLogger(__name__)

class SpreadHandler():
    
    def __init__(self, spreadsheet_key: str):
        # fetch credentials from google and store them locally for now
        gc = gspread.service_account(filename='credentials.json')

        self.gsheet = gc.open_by_key(spreadsheet_key)
        
    def prep_sheet(self, title, headers, info) -> bool:
        logger.info(f'Preparing to create sheet {title}')
        try:
            wsheet = self.gsheet.add_worksheet(title, 200, 32)
        except gspread.exceptions.APIError:
            logger.info(f'Not adding a new sheet, instead using {title}')
            wsheet = self.gsheet.worksheet(title)
            # def for a larger number
            wsheet.batch_clear(['A1:K500'])
        wsheet.insert_row(headers, 1)
        wsheet.insert_rows(info, 2)
        return True

    def write(self, title, data, headers):
        for region, locations in data.items():
            values = len(locations.keys())
            if(values > 0):
                logger.info(f'Attempting to write {values}')
                info = []
                for name, location in locations.items():
                    for price, prop in location.items():
                        logger.info(f'Writing {price}: {prop.title}')
                        info.append(prop.to_csv())
                self.prep_sheet(f'{title}- {region}', headers, info)