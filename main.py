import os
import logging
import sys

from datetime import datetime
from sendinblue import Sendinblue
from rightmove import RightMoveScrapper
from regions import REGIONS
from spreadsheet import SpreadHandler

# process env variables
sendinblue_key = os.getenv('SENDINBLUE_KEY', '')
sendinblue_receivers = os.getenv('SENDINBLUE_TO', '').split(",")
sendinblue_sender = os.getenv('SENDINBLUE_FROM', '')
timer = os.getenv('SENDINBLUE_TIME', '')
radius = os.getenv('RIGHTMOVE_RADIUS', '3')
local =  os.getenv('LOCAL', True)
sendinblue = os.getenv('SENDINBLUE', False)
sheet_key = os.getenv('SHEET_KEY', "1Md11UVIOUdkSGiALuNRiTp1Ag_jddWYRrOQkS_35xz0")

# sendinblue api
s = Sendinblue(
    sendinblue_key,
    sendinblue_sender,
    sendinblue_receivers
)


global logger
logger=logging.getLogger()

def set_logger():
    print(f"Initialising logger {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}") 
    logging.basicConfig(level=logging.INFO)

def process_data(scrapper: RightMoveScrapper, regions: dict):
    logger.info(f'Starting property processing  task at {datetime.now()}.')
    for region in regions.keys():
        locations = regions[region]
        try:
            scrapper_locations = scrapper.regions[region]
        except KeyError:
            logger.info(f'Tried fetching properties list for {region}, but it was uninitiliased. Setting as empty.')
            scrapper_locations = {}
            scrapper.regions[region] = scrapper_locations
        for location, location_code in locations.items():
            print(f'Processing {location}: {location_code}')
            properties = {}
            properties.update(scrapper.query_houses(region, location, location_code, radius))
            scrapper_locations[location] = properties
            print(f'Found {len(properties)} for {location}')
        scrapper.regions[region] = scrapper_locations
    properties_html = scrapper.get_properties_html()
    success = False
    if sendinblue:
        if local:
            with open('results/result.html', 'w') as f:
                f.write(properties_html)
                f.close()
                success = True
        else:
            success = s.send(properties_html)
        if success:
            logger.info(f'Finished property processing  task at {datetime.now()}.')
    else:
        s = SpreadHandler(sheet_key)
        s.write(datetime.now().strftime("%m/%d/%Y"), scrapper.regions,  ['Price','Title','Monthly','Location','Added','Type','Bedroom','Bathrooms'])

rightmove = RightMoveScrapper(user_agent="This is a web scraper")

set_logger()
process_data(rightmove, REGIONS)
