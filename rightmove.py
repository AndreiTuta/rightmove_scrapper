import os
import requests

from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass
from apscheduler.schedulers.background import BackgroundScheduler

from jinja2 import Template
from sendinblue import Sendinblue

path = 'results'

BASE = "div#root>main>div._38rRoDgM898XoMhNRXSWGq>div.WJG_W7faYk84nW-6sCBVi>div._1kesCpEjLyhQyzhf_suDHz"
RIGHT_MOVE_PRICE = BASE + ">article._2fFy6nQs_hX4a6WEDR-B-6>div._5KANqpn5yboC4UXVUxwjZ>div._3Kl5bSUaVKx1bidl6IHGj7>div._1gfnqJ3Vtd1z40MlC0MzXu>span"
RIGHT_MOVE_LOCATIONS = BASE + ">div.H2aPmrbOxrd-nTRANQzAY>div._1KCWj_-6e8-7_oJv_prX0H>div.h3U6cGyEUf76tvCpYisik>h1._2uQQ3SV0eMHL1P6t5ZDo2q"
RIGHT_MOVE_ADDED = BASE + ">article._2fFy6nQs_hX4a6WEDR-B-6>div._5KANqpn5yboC4UXVUxwjZ>div._3Kl5bSUaVKx1bidl6IHGj7>div._1NmnYm1CWDZHxDfsCNf-WJ>div._1q3dx8PQU8WWiT7uw7J9Ck>div._2nk2x6QhNB1UrxdI5KpvaF"
RIGHT_MOVE_STATIONS = BASE + ">div._3v_yn6n1hMx6FsmIoZieCM>div#Stations-panel._2CdMEPuAVXHxzb5evl1Rb8>ul._2f-e_tRT-PqO8w8MBRckcn>li"
RIGHT_MOVE_FEATURES = BASE + ">article>div._4hBezflLdgDMdFtURKTWh>div._1u12RxIYGx3c84eaGxI6_b>div._3mqo4prndvEDFoh4cDJw_n>div._2Pr4092dZUG6t1_MyGPRoL>div._1fcftXUEbWfJOJzIUeIHKt"

# process env variables
sendinblue_key = os.environ['SENDINBLUE_KEY']
sendinblue_receiver = os.environ['SENDINBLUE_TO']
sendinblue_sender = os.environ['SENDINBLUE_FROM']
timer = os.environ['SENDINBLUE_TIME']

# properties dict
properties = {}
# sendinblue api
s = Sendinblue(
    sendinblue_key,
    sendinblue_sender,
    sendinblue_receiver
)

class SearchScraper:
    def __init__(
            self,
            page_param,
            per_page,
            get_item_link_list_func,
            user_agent,
            start_page=0
    ):
        self.page_param = page_param
        self.per_page = per_page
        self.get_item_link_list_func = get_item_link_list_func
        self.user_agent = user_agent
        self.start_page = start_page

    def search(self, starting_endpoint, params={}, v=False):
        page = int(self.start_page)
        while True:
            print("Processing page {}".format(page))
            links = self.get_item_link_list_func(
                self.get(starting_endpoint, page, params)
            )
            if not links:
                print("Finished searching")
                break
            for link in links:
                yield link, self.get(link)
            page = page + self.per_page

    def get(self, endpoint, page=0, params={}):
        headers = {
            'User-Agent': self.user_agent
        }
        if page:
            params[self.page_param] = page
        while True:
            try:
                r = requests.get(endpoint, headers=headers, params=params)
            except Exception as e:
                print("Couldn't connect, retrying...")
                continue
            r.raise_for_status()
            break
        return r.text

class Rightmove:
    def __init__(self, user_agent):
        self.params = {
            'searchType': 'RENT',
            'insId': '1',
            'radius': '0.0',
            'minPrice': '',
            'maxPrice': '100',
            'minBedrooms': '2',
            'maxDaysSinceAdded': '7',
            # '_includeSSTC': 'on'
        }
        self.endpoint = "http://www.rightmove.co.uk/"
        self.endpoint_rent_search = "property-for-rent/find.html"
        self.endpoint_sale_search = "property-for-sale/find.html"

        self.scraper = SearchScraper(
            page_param="index",
            per_page=10,
            get_item_link_list_func=lambda html: set([
                self.endpoint + x['href'] for x in
                BeautifulSoup(html, "html.parser").find_all(
                    "a",
                    attrs={'class': 'propertyCard-link'}
                ) if x['href']
            ]),
            user_agent=user_agent
        )

    def search(self, region, params={}, rent=False):
        query_properties = {}
        merged_params = self.params.copy()
        merged_params.update(params)
        starting_endpoint = self.endpoint
        # get the region code
        if rent:
            starting_endpoint = starting_endpoint + self.endpoint_rent_search
        else:
            starting_endpoint = starting_endpoint + self.endpoint_sale_search
        for link, rental_property_html in self.scraper.search(
                starting_endpoint,
                merged_params,
                True
        ):
            soup = BeautifulSoup(rental_property_html, "html.parser")
            try:
                price = (soup.select(RIGHT_MOVE_PRICE)[0]).text
                location = (soup.select(RIGHT_MOVE_LOCATIONS)[0]).text
                added = (soup.select(RIGHT_MOVE_ADDED)[0]).text
                prop_type = (soup.select(RIGHT_MOVE_FEATURES)[0]).text
                bedrooms = (soup.select(RIGHT_MOVE_FEATURES)[1]).text
                bathrooms = (soup.select(RIGHT_MOVE_FEATURES)[2]).text
                stations = []
                for station_text in soup.select(RIGHT_MOVE_STATIONS):
                    station_text = BeautifulSoup(station_text.text, "html.parser").text.split("Station")
                    stations.append(" ".join(station_text))
                title = soup.title.text
                new = title not in properties[region].keys()
                p = Property(new, price, location, title, added, stations, prop_type, bedrooms, bathrooms, link.replace('//properties','/properties'))
                query_properties[p.title] = p
            except IndexError as e:
                print(f"Error: {str(e)}")
        # post processing
        return query_properties

@dataclass
class Property():
    new: bool
    price: str
    location: str
    title: str
    added: str
    stations: list
    prop_type: str
    bedrooms: str
    bathrooms: str
    url: str

def query_houses(region, region_code):
    new_properties = {}
    print(f"Starting house search in region {region} at {datetime.now()}...")
    for key,property in rightmove.search(region, {"radius": "1.0",
            'searchType': 'SALE',
            'locationIdentifier': "REGION^"+region_code,
            'minBedrooms': '3',
            'maxPrice': '200000'},
            False).items():
            print(f"Adding a new property {key} to property list")
            new_properties[key] = property
    return new_properties

def get_properties_html(properties):
    with open('template.html.jinja2') as file_:
        # fetch jinja template
        template = Template(file_.read())
    # render it
    return template.render(properties=properties)

def process_data():
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
    print(f'Starting property processing  task at {datetime.now()}.')
    for region, region_code in regions.items():
        try:
            props = properties[region]
        except KeyError:
            print(f'Tried fetching properties list for {region}, but it was uninitiliased. Setting as empty.')
            properties[region] = {}
            props = {}
        new_props = query_houses(region, region_code)
        props.update(new_props)
        properties[region] = props
    properties_html = get_properties_html(properties)
    success = s.send(properties_html)
    # with open('results/result.html', 'w') as f:
        # f.write(properties_html)
    if success:
        print(f'Finished property processing  task at {datetime.now()}.')

scheduler = BackgroundScheduler(timezone="Europe/London")
rightmove = Rightmove(user_agent="This is a web scraper")

process_data()
# add the job and run the scheduler
scheduler.add_job(process_data, 'interval', minutes=int(timer))
scheduler.start()


while True:
    pass