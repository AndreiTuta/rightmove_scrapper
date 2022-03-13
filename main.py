import os
import logging
import sys

from datetime import datetime
from sendinblue import Sendinblue
from rightmove import RightMoveScrapper, Property
from regions import REGIONS

# process env variables
# Sendinblue config - used to send HTML table of results in emails
sendinblue_key = os.getenv('SENDINBLUE_KEY', '')
sendinblue_receivers = os.getenv('SENDINBLUE_TO', '').split(",")
sendinblue_sender = os.getenv('SENDINBLUE_FROM', '')
# SPREADSHEETS
sheet_key = os.getenv('SHEET_KEY', "1Md11UVIOUdkSGiALuNRiTp1Ag_jddWYRrOQkS_35xz0")
# SEARCH constants
RADIUS = os.getenv('RIGHTMOVE_RADIUS', '5')
MAX_PRICE = os.getenv('RIGHTMOVE_MAX', '250000')
# Runtime conf
# Save html as file or send via Sendinblue
LOCAL =  os.getenv('LOCAL', True)
# Use spreadsheets/html
PROCESS_HTML = os.getenv('PROCESS_HTML', False)

# sendinblue api
s = Sendinblue(
    sendinblue_key,
    sendinblue_sender,
    sendinblue_receivers
)

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
        scrapper.setup(region=region, locations=locations, radius=RADIUS, max_price=MAX_PRICE)
    success = False
    if PROCESS_HTML:
        properties_html = scrapper.get_properties_html()
        if LOCAL:
            with open('results/result.html', 'w') as f:
                f.write(properties_html)
                f.close()
                success = True
        else:
            success = s.send(properties_html)
    else:
        logging.info(f"Preparing to write")
        # covered in spreasheet branch
        success = True
    if success:
        logger.info(f'Finished property processing task on date {RUNTIME}.')

if __name__ == "__main__":
    rightmove = RightMoveScrapper(user_agent="This is a web scraper")
    process_data(rightmove, REGIONS)
