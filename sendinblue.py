import requests
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class Sendinblue():
    def __init__(self, api, from_address, to_addresses):
        self.url = "https://api.sendinblue.com/v3/smtp/email"
        self.api = api
        self.from_address = from_address
        self.to_addresses = to_addresses

    def make_sendinblue_email_call(self, to_address, html):
        logging.debug(f"Preparing to send email to {to_address}.")
        payload = json.dumps({
        "sender": {
            "email": self.from_address
        },
        "to": [
            {
            "email": to_address
            }
        ],
        "htmlContent": html,
        "subject": f"Rightmove houses@{datetime.now().strftime('%d/%m/%Y, %H:%M')}"
        })
        headers = {
        'api-key': self.api,
        'Content-Type': 'application/json'
        }
        logger.debug(f"Sendinblue request payload: {payload}")
        logger.debug(f"Sendinblue request headers: {headers}")
        return requests.request("POST", self.url, headers=headers, data=payload)

    def send(self, html):
        logging.debug(f"Preparing to send email to {len(self.to_addresses)} emails.")
        success = True
        for to_address in  self.to_addresses:
            response = self.make_sendinblue_email_call(to_address, html)
            logger.debug(f"Sendinblue response: {response.text}")
            if (response.status_code == 201):
                logging.info(f"Sent email to {to_address}")
            else:
                logging.error(f"Failed to send email to {to_address}")
                success = False
        return success