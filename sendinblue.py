import requests
import json

class Sendinblue():
    def __init__(self, api, from_address, to_address):
        self.url = "https://api.sendinblue.com/v3/smtp/email"
        self.api = api
        self.from_address = from_address
        self.to_address = to_address

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
        "subject": "Rightmove houses"
        })
        headers = {
        'api-key': self.api,
        'Content-Type': 'application/json'
        }

        response = requests.request("POST", self.url, headers=headers, data=payload)

        return response.status_code == 201