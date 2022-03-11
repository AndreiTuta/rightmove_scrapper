from bs4 import BeautifulSoup
from datetime import datetime
from dataclasses import dataclass
from jinja2 import Template

from scrapper import SearchScraper
import logging

import re
import collections

logger = logging.getLogger(__name__)

BASE = "div#root>main>div._38rRoDgM898XoMhNRXSWGq>div.WJG_W7faYk84nW-6sCBVi>div._1kesCpEjLyhQyzhf_suDHz"
RIGHT_MOVE_PRICE = BASE + \
    ">article._2fFy6nQs_hX4a6WEDR-B-6>div._5KANqpn5yboC4UXVUxwjZ>div._3Kl5bSUaVKx1bidl6IHGj7>div._1gfnqJ3Vtd1z40MlC0MzXu>span"
RIGHT_MOVE_LOCATIONS = BASE + \
    ">div.H2aPmrbOxrd-nTRANQzAY>div._1KCWj_-6e8-7_oJv_prX0H>div.h3U6cGyEUf76tvCpYisik>h1._2uQQ3SV0eMHL1P6t5ZDo2q"
RIGHT_MOVE_ADDED = BASE + ">article._2fFy6nQs_hX4a6WEDR-B-6>div._5KANqpn5yboC4UXVUxwjZ>div._3Kl5bSUaVKx1bidl6IHGj7>div._1NmnYm1CWDZHxDfsCNf-WJ>div._1q3dx8PQU8WWiT7uw7J9Ck>div._2nk2x6QhNB1UrxdI5KpvaF"
RIGHT_MOVE_STATIONS = BASE + \
    ">div._3v_yn6n1hMx6FsmIoZieCM>div#Stations-panel._2CdMEPuAVXHxzb5evl1Rb8>ul._2f-e_tRT-PqO8w8MBRckcn>li"
RIGHT_MOVE_FEATURES = BASE + ">article>div._4hBezflLdgDMdFtURKTWh>div._1u12RxIYGx3c84eaGxI6_b>div._3mqo4prndvEDFoh4cDJw_n>div._2Pr4092dZUG6t1_MyGPRoL>div._1fcftXUEbWfJOJzIUeIHKt"
RIGHT_MOVE_MONTHLY = "div#root>div._1tLR5kRoqLZPySCrk5HnOD>div._34vDaCz_NZuPJRjS5XJVXh>span.A8pd_b9E9GHaNUK-GSdwz"


class RightMoveScrapper:
    def __init__(self, user_agent):
        self.params = {
            'searchType': 'RENT',
            'insId': '1',
            'radius': '0.0',
            'minPrice': '',
            'maxPrice': '100',
            'minBedrooms': '2',
            'maxDaysSinceAdded': '3',
            # '_includeSSTC': 'on'
        }
        # properties dict
        self.regions = {}
        self.endpoint = "http://www.rightmove.co.uk/"
        self.endpoint_rent_search = "property-for-rent/find.html"
        self.endpoint_sale_search = "property-for-sale/find.html"

        self.scraper = SearchScraper(
            page_param="index",
            per_page=1,
            get_item_link_list_func=lambda html: set([
                self.endpoint + x['href'] for x in
                BeautifulSoup(html, "html.parser").find_all(
                    "a",
                    attrs={'class': 'propertyCard-link'}
                ) if x['href']
            ]),
            user_agent=user_agent, start_page=0, max=1
        )

    def query_rightmove(self, region, params={}, rent=False):
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
                location = (soup.select(RIGHT_MOVE_LOCATIONS)[0]).text
                # update link by removing double backslash
                link = link.replace("//properties", "/properties")
                # generate map link by appending query param
                map_location = link.replace(
                    "?channel=RES_BUY", "map?channel=RES_BUY")
                # extract the property id from the link
                prop_ids = re.findall(r'\d+', link)
                prop_id = prop_ids[0]
                # use the id to get the contact form
                contact_url = f"{self.endpoint}/property-for-sale/contactBranch.html?backToPropertyURL=%2Fproperties%2F{prop_id}&propertyId={prop_id}"
                # property attributes
                added = (soup.select(RIGHT_MOVE_ADDED)[0]).text
                prop_type = (soup.select(RIGHT_MOVE_FEATURES)[0]).text
                bedrooms = (soup.select(RIGHT_MOVE_FEATURES)[1]).text
                bathrooms = (soup.select(RIGHT_MOVE_FEATURES)[2]).text
                # get price and value
                price = (soup.select(RIGHT_MOVE_PRICE)[0]).text
                # montly payment
                # create url for mortgage scrapper and soup
                safe_price = price.replace(',', '').replace('£', '')
                mortgage_url = f"{self.endpoint}/mortgage-calculator?price={safe_price}&propertyType=houses&showStampDutyCalculator=true"
                mortgage_soup = BeautifulSoup(
                    self.scraper.get(mortgage_url), "html.parser")
                # get price and strip everything but value
                monthly_payment = (mortgage_soup.select(
                    RIGHT_MOVE_MONTHLY)[0]).text
                monthly_payment = (re.findall(r'\d+', monthly_payment))[0]
                stations = []
                for station_text in soup.select(RIGHT_MOVE_STATIONS):
                    station_text = BeautifulSoup(
                        station_text.text, "html.parser").text
                    if 'Station' in station_text:
                        station_text = station_text.split("Station")
                    elif 'Stop' in station_text:
                        station_text = station_text.split("Stop")
                    stations.append(" ".join(station_text))
                title = soup.title.text
                p = Property(False, price[1:], monthly_payment, location, map_location, title,
                             added, stations, prop_type, bedrooms, bathrooms, link, contact_url)
                query_properties[p.price] = p
            except IndexError as e:
                logger.error(
                    f"Error: Error processing property {starting_endpoint + self.endpoint_rent_search}. Ommiting")
        # post processing
        return collections.OrderedDict(sorted(query_properties.items()))

    def check_property_exists(self, key, property):
        logger.info(f'Checking if property {key} exists in other regions.')
        for region, properties in self.regions.items():
            print(f'Checking for {region}...')
            for location, prop_dict in properties.items():
                for prop_key in prop_dict.keys():
                    if(prop_key == key):
                        logger.info(
                            f"Prop {key} already exists in location {location}")
                        return None
        logger.info(f"Adding a new property {key} to property list")
        return property

    def query_houses(self, region, location, location_code, radius):
        new_properties = {}
        logger.info(
            f"Starting house search in location {location} at {datetime.now()}...")
        for key, property in self.query_rightmove(location, {"radius": radius,
                                                             'searchType': 'SALE',
                                                             'locationIdentifier': "REGION^"+location_code,
                                                             'minBedrooms': '3',
                                                             'maxPrice': '200000'},
                                                  False).items():
            # property = self.check_property_exists(key, property)
            if(property is not None):
                new_properties[key] = property
        return new_properties

    def get_properties_html(self):
        with open('template.html.jinja2') as file_:
            # fetch jinja template
            template = Template(file_.read())
        # render it
        return template.render(regions=self.regions)


@dataclass
class Property():
    new: bool
    price: str
    monthly_payment: str
    location: str
    map_location: str
    title: str
    added: str
    stations: list
    prop_type: str
    bedrooms: str
    bathrooms: str
    url: str
    contact_url: str
