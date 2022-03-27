import os
import logging

from datetime import datetime
from rightmove import RightMoveScrapper, Property
from regions import REGIONS
from spreadsheet import SpreadHandler

# process env variables
sheet_key = os.getenv('SHEET_KEY', "1Md11UVIOUdkSGiALuNRiTp1Ag_jddWYRrOQkS_35xz0")
# SEARCH constants
RADIUS = os.getenv('RIGHTMOVE_RADIUS', '15.0')
MAX_PRICE = os.getenv('RIGHTMOVE_MAX', '250000')
SCRAP_TYPE =  os.getenv('STYPE', "RENT")
# Runtime conf
# Save html as file/send via Sendinblue
LOCAL =  os.getenv('LOCAL', True)
# Use html/spreadsheets
PROCESS_HTML = os.getenv('PROCESS_HTML', False)

RUNTIME = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

def set_logger():
    print(f"Initialising logger {RUNTIME}") 
    logging.basicConfig(level=logging.INFO)

global logger
logger=logging.getLogger()

set_logger()

def process_data(scrapper: RightMoveScrapper, regions: dict):
    logger.info(f'Starting property processing  task at {RUNTIME}.')
    for region in regions.keys():
        locations = regions[region]
        scrapper.setup(region=region, locations=locations, radius=RADIUS, max_price=MAX_PRICE, scrap_type=SCRAP_TYPE)
    success = False
    if PROCESS_HTML:
        properties_html = scrapper.get_properties_html()
        if LOCAL:
            with open('results/result.html', 'w') as f:
                f.write(properties_html)
                f.close()
                success = True
        else:
            # covered by sendinblue branch
            success = True
            pass
    else:
        logging.info(f"Preparing to write")
        s = SpreadHandler(sheet_key)
        date = RUNTIME[:10]
        s.write(f"{SCRAP_TYPE} at{date}", scrapper.regions, Property.HEADERS)
        success = True
    if success:
        logger.info(f'Finished property processing task on date {RUNTIME}.')

if __name__ == "__main__":
    rightmove = RightMoveScrapper(user_agent="This is a web scraper")
    process_data(rightmove, REGIONS)
