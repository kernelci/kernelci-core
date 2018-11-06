#!/usr/bin/python

"""Send a boot email report in 60 seconds in TXT and HTML formats."""

try:
    import simplejson as json
except ImportError:
    import json

import requests

from urlparse import urljoin

BACKEND_URL = "https://api.kernelci.org"
AUTHORIZATION_TOKEN = "foo"


def main():
    headers = {
        "Authorization": AUTHORIZATION_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "job": "next",
        "kernel": "next-20150105",
        "boot_report": 1,
        "send_to": ["email1@example.org", "email2@example.org"],
        "delay": 60,
        "format": ["txt", "html"]
    }

    url = urljoin(BACKEND_URL, "/send")
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    print response.content


if __name__ == "__main__":
    main()
