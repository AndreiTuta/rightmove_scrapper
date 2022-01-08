import requests
import json
import logging

logger = logging.getLogger(__name__)

class Sendinblue():
    def __init__(self, api, from_address, to_address, date):
        self.url = "https://api.sendinblue.com/v3/smtp/email"
        self.api = api
        self.from_address = from_address
        self.to_address = to_address
        self.date = date

    def send(self, html):
        payload = json.dumps({
        "sender": {
            "email": self.from_address
        },
        "to": [
            {
            "email": self.to_address
            }
        ],
        "htmlContent": html,
        "subject": f"Rightmove houses {self.date}"
        })
        headers = {
        'api-key': self.api,
        'Content-Type': 'application/json'
        }
        logger.debug(f"Sendinblue request payload: {payload}")
        logger.debug(f"Sendinblue request headers: {headers}")

        response = requests.request("POST", self.url, headers=headers, data=payload)
        logger.debug(f"Sendinblue response: {response.text}")
        return response.status_code == 201
