import os
import logging
import subprocess

from datetime import datetime
from rightmove import RightMoveScrapper
from regions import REGIONS

# process env variables
# SEARCH constants
RADIUS = os.getenv('RIGHTMOVE_RADIUS', '40')
BEDS = os.getenv('RIGHTMOVE_BEDS', '2')
MAX_PRICE = os.getenv('RIGHTMOVE_MAX', '80000')
TYPE = os.getenv('RIGHTMOVE_PROP_TYPE', 'flats')

RUNTIME = datetime.now().strftime("%d/%m/%Y, %H:%M:%S")

def set_logger():
    print(f"Initialising logger {RUNTIME}") 
    logging.basicConfig(level=logging.INFO)

global logger
logger=logging.getLogger()

set_logger()

def open_chromium_tabs(date: str, region: str):
    logger.info(f'Opening results for [{region}]')
    f = open(f"results/{date}-{region}.txt", "r")
    links = [x.strip() for x in f]
    s=''
    for l in links:
        s=f'{s} {l}'
    subprocess.run(f"nohup chromium {s}", shell=True)

def process_data(scrapper: RightMoveScrapper, regions: dict):
    logger.info(f'Starting property processing  task at {RUNTIME}.')
    date = datetime.now().strftime("%m-%d-%Y")
    for region in regions.keys():
        locations = regions[region]
        scrapper.setup(region=region, 
                       locations=locations, 
                       radius=RADIUS, 
                       max_price=MAX_PRICE,
                       beds=BEDS, 
                       types=TYPE,
                       date=date)
        logger.info(f'Finished property processing task on date {RUNTIME}.')
        logger.info(f'Opening results from results/{date}.txt in chromium')
        open_chromium_tabs(date, region)

if __name__ == "__main__":
    rightmove = RightMoveScrapper(user_agent="This is a web scraper")
    process_data(rightmove, REGIONS)
