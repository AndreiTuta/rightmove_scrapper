import os
import logging
import sys

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sendinblue import Sendinblue
from rightmove import RightMoveScrapper
from regions import REGIONS

# process env variables
sendinblue_key = os.environ['SENDINBLUE_KEY']
sendinblue_receivers = (os.environ['SENDINBLUE_TO']).split(",")
sendinblue_sender = os.environ['SENDINBLUE_FROM']
timer = os.environ['SENDINBLUE_TIME']
radius = os.environ['RIGHTMOVE_RADIUS']
local = False

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
    if local:
        with open('results/result.html', 'w') as f:
            f.write(properties_html)
            f.close()
            success = True
    else:
        success = s.send(properties_html)
    if success:
        logger.info(f'Finished property processing  task at {datetime.now()}.')

scheduler = BackgroundScheduler(timezone="Europe/London")
rightmove = RightMoveScrapper(user_agent="This is a web scraper")

# add the job and run the scheduler
# scheduler.add_job(process_data, 'interval', minutes=int(timer), args=[rightmove, REGIONS])

set_logger()
process_data(rightmove, REGIONS)
scheduler.start()

while True:
    pass
