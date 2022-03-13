import os
import logging
import sys

from datetime import datetime
from rightmove import RightMoveScrapper, Property
from regions import REGIONS

# process env variables
# SEARCH constants
RADIUS = os.getenv('RIGHTMOVE_RADIUS', '5')
MAX_PRICE = os.getenv('RIGHTMOVE_MAX', '250000')
# Runtime conf
# Save html as file or send via Sendinblue
LOCAL =  os.getenv('LOCAL', True)
# Use spreadsheets/html
PROCESS_HTML = os.getenv('PROCESS_HTML', LOCAL)

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
            # covered by sendinblue branch
            success = True
            pass
    else:
        logging.info(f"Preparing to write")
        # covered by spreadsheet branch
        success = True
    if success:
        logger.info(f'Finished property processing task on date {RUNTIME}.')

if __name__ == "__main__":
    rightmove = RightMoveScrapper(user_agent="This is a web scraper")
    process_data(rightmove, REGIONS)
