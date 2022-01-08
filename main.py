import os
import logging
import sys

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
# sendinblue api
s = Sendinblue(
    sendinblue_key,
    sendinblue_sender,
    sendinblue_receiver,
    datetime.now().strftime("%d/%m/%Y, %H:%M:%S")
)


global logger
logger=logging.getLogger()

def set_logger():
    print(f"Initialising logger {datetime.now().strftime('%d/%m/%Y, %H:%M:%S')}")
    formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
    handler = logging.StreamHandler(sys.stdout)  
    handler.setFormatter(formatter)
    handler.setLevel(logging.DEBUG)
    logging.basicConfig(level=logging.INFO)
    logger.addHandler(handler)

regions = {
"Buxton": '261',
"Chapel-en-le-Frith": '6005',
"Crewe": '380',
"Glossop": '555',
"Hazel Grove":'12188',
"Hyde":'66185',
"Macclesfield":'890',
"New Mills":'18107',
"Stockport":'1268',
"Poynton": '20226',
"Wimslow": '1456',
"Wythenshaw": '27637',
}

def process_data(scrapper: RightMoveScrapper, regions: dict):
    set_logger()
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

scheduler = BackgroundScheduler(timezone="Europe/London")
rightmove = RightMoveScrapper(user_agent="This is a web scraper")

# add the job and run the scheduler
scheduler.add_job(process_data, 'interval', minutes=int(timer), args=[rightmove, regions])

process_data(rightmove, regions)
scheduler.start()

while True:
    pass