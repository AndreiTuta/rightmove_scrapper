import os
import logging

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from sendinblue import Sendinblue
from rightmove import RightMoveScrapper

path = 'results'

# process env variables
sendinblue_key = os.environ['SENDINBLUE_KEY']
sendinblue_receiver = os.environ['SENDINBLUE_TO']
sendinblue_sender = os.environ['SENDINBLUE_FROM']
timer = os.environ['SENDINBLUE_TIME']
timer = 5
# sendinblue api
s = Sendinblue(
    sendinblue_key,
    sendinblue_sender,
    sendinblue_receiver
)


global logger
logger=logging.getLogger()

def set_logger():
    print(f"Initialising logger {datetime.now()}")
    file_handler = logging.FileHandler(os.path.join('logs','logfile.log'), mode="w")
    formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    logger.setLevel(logging.DEBUG)

regions = {
"Crewe": '380',
"Glossop": '555',
"Hazel Grove":'12188',
"Hyde":'66185',
"Macclesfield":'890',
"New Mills":'18107',
"Stockport":'1268',
"Poynton": '20226',
"Wythenshaw": '27637'
}

def process_data(scrapper: RightMoveScrapper, regions: dict):
    logger.info(f'Starting property processing  task at {datetime.now()}.')
    for region, region_code in regions.items():
        try:
            props = scrapper.properties[region]
        except KeyError:
            logger.info(f'Tried fetching properties list for {region}, but it was uninitiliased. Setting as empty.')
            scrapper.properties[region] = {}
            props = {}
        new_props = scrapper.query_houses(region, region_code)
        props.update(new_props)
        scrapper.properties[region] = props
    properties_html = scrapper.get_properties_html()
    success = False
    success = s.send(properties_html)
    # with open('results/result.html', 'w') as f:
    #     f.write(properties_html)
    #     f.close()
    #     success = True
    if success:
        logger.info(f'Finished property processing  task at {datetime.now()}.')

set_logger()
scheduler = BackgroundScheduler(timezone="Europe/London")
rightmove = RightMoveScrapper(user_agent="This is a web scraper")

# add the job and run the scheduler
scheduler.add_job(process_data, 'interval', minutes=int(timer), args=[rightmove, regions])

process_data(rightmove, regions)
scheduler.start()

while True:
    pass