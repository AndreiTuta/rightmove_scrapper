from bs4 import BeautifulSoup
from datetime import datetime

from scrapper import SearchScraper
import logging
import os

logger = logging.getLogger(__name__)

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
        
    def setup(self, region: str, locations: dict, radius: str, max_price: str, beds:int, types: str, date: str):
        properties = {}
        for location, location_code in locations.items():
            logger.info(f'Processing {location}: {location_code}')
            new_properties = self.query_houses(region, location, location_code, radius=radius, maxPrice = max_price, beds=beds, types=types, date=date)
            for p in new_properties:
                logger.info(f'Adding [{p}]')
                properties[p] = True
        logger.info(f'Found {len(properties)} for {location}')
        logger.info(f'Updating {region}')
        self.regions[region] = properties
        self.record_data(properties, region, date)

    def record_data(self, properties, region, date):
        path = f'results/{date}-{region}.txt'
        try:
            os.remove(path)
        except:
            logger.info(f'File {path} does not exist')
        with(open(path, 'a+')) as f:
            for link in properties.keys():
                f.write(f'{link}\n')

    def sanitize_link(self, url_of_soup: str):
        # sanitize link
        return url_of_soup.replace("//properties", "/properties")

    def query_rightmove(self, date, params={}, rent=False):
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
            p = self.sanitize_link(link)
            query_properties[link] = p
        return query_properties

    def query_houses(self, region, location, location_code, radius, maxPrice, beds, types, date):
        new_properties = []
        logger.info(
            f"Starting house search in location {region} - {location} at {datetime.now()}...")
        for key, property in self.query_rightmove(date, {"radius": radius,
                                                             'searchType': 'SALE',
                                                             'locationIdentifier': "REGION^"+location_code,
                                                             'minBedrooms': beds,
                                                             'maxPrice': maxPrice,
                                                             'displayPropertyType': types},
                                                  False).items():
            logger.info(f'Found [{property}]')
            new_properties.append(property)
        return new_properties