import os

from bs4 import BeautifulSoup
import requests

path = 'results'

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
                yield self.get(link)
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

    def search(self, params={}, rent=False):
        merged_params = self.params.copy()
        merged_params.update(params)
        starting_endpoint = self.endpoint
        if rent:
            starting_endpoint = starting_endpoint + self.endpoint_rent_search
        else:
            starting_endpoint = starting_endpoint + self.endpoint_sale_search
        for rental_property_html in self.scraper.search(
                starting_endpoint,
                merged_params,
                True
        ):
            soup = BeautifulSoup(rental_property_html, "html.parser")
            price = (soup.select("div#root>main>div._38rRoDgM898XoMhNRXSWGq>div.WJG_W7faYk84nW-6sCBVi>div._1kesCpEjLyhQyzhf_suDHz>article._2fFy6nQs_hX4a6WEDR-B-6>div._5KANqpn5yboC4UXVUxwjZ>div._3Kl5bSUaVKx1bidl6IHGj7>div._1gfnqJ3Vtd1z40MlC0MzXu>span")[0]).text
            location = (soup.select("div#root>main>div._38rRoDgM898XoMhNRXSWGq>div.WJG_W7faYk84nW-6sCBVi>div._1kesCpEjLyhQyzhf_suDHz>div.H2aPmrbOxrd-nTRANQzAY>div._1KCWj_-6e8-7_oJv_prX0H>div.h3U6cGyEUf76tvCpYisik>h1._2uQQ3SV0eMHL1P6t5ZDo2q")[0]).text
            added = (soup.select("div#root>main>div._38rRoDgM898XoMhNRXSWGq>div.WJG_W7faYk84nW-6sCBVi>div._1kesCpEjLyhQyzhf_suDHz>article._2fFy6nQs_hX4a6WEDR-B-6>div._5KANqpn5yboC4UXVUxwjZ>div._3Kl5bSUaVKx1bidl6IHGj7>div._1NmnYm1CWDZHxDfsCNf-WJ>div._1q3dx8PQU8WWiT7uw7J9Ck>div._2nk2x6QhNB1UrxdI5KpvaF")[0]).text
            stations = []
            for station_text in soup.select("div#root>main>div._38rRoDgM898XoMhNRXSWGq>div.WJG_W7faYk84nW-6sCBVi>div._1kesCpEjLyhQyzhf_suDHz>div._3v_yn6n1hMx6FsmIoZieCM>div#Stations-panel._2CdMEPuAVXHxzb5evl1Rb8>ul._2f-e_tRT-PqO8w8MBRckcn>li"):
                stations.append(BeautifulSoup(station_text.text, "html.parser").text)
            title = soup.title.text
            print(stations)
            print(price, location, title, added)
            with open(f'{path}/'+soup.title.text+".html", 'w') as f:
                f.write(rental_property_html)


if __name__ == "__main__":

    rightmove = Rightmove(
        user_agent="This is a web scraper"
    )

    print(f'* Removing files from {path} *')
    for root, dirs, files in os.walk(path):
        for file in files:
            os.remove(os.path.join(root, file))

    print("Starting house search...")
    rightmove.search({"radius": "0.0",
            'searchType': 'SALE',
            'locationIdentifier': 'REGION^1268',
            'minBedrooms': '3',
            'maxPrice': '200000'},
            False)