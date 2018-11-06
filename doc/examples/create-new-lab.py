#!/usr/bin/python

"""Create a new lab entry."""

try:
    import simplejson as json
except ImportError:
    import json

import requests
import urlparse

BACKEND_URL = "https://api.kernelci.org"
AUTHORIZATION_TOKEN = "foo"


def main():
    headers = {
        "Authorization": AUTHORIZATION_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "name": "lab-enymton",
        "contact": {
            "name": "Ema",
            "surname": "Nymton",
            "email": "ema.nymton@example.org"
        }
    }

    url = urlparse.urljoin(BACKEND_URL, "/lab")
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    print response.content


if __name__ == "__main__":
    main()
