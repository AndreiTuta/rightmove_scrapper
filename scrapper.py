import requests 

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
        print(f"Creating new scrapper for {self.user_agent}")

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
            print(f"Found {len(links)} links")
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