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
        print(f"Sendinblue request payload: {payload}")
        print(f"Sendinblue request headers: {headers}")

        response = requests.request("POST", self.url, headers=headers, data=payload)
        print(f"Sendinblue response: {response.text}")
        return response.status_code == 201
