#!/usr/bin/python

"""Get all boot reports for a job and a specified kernel."""

import requests

from urlparse import urljoin

BACKEND_URL = "https://api.kernelci.org"
AUTHORIZATION_TOKEN = "foo"


def main():
    headers = {
        "Authorization": AUTHORIZATION_TOKEN
    }

    params = {
        "job": "next",
        "kernel": "next-20150717"
    }

    url = urljoin(BACKEND_URL, "/boot")
    response = requests.get(url, params=params, headers=headers)

    print response.content


if __name__ == "__main__":
    main()
