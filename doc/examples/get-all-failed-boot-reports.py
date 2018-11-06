#!/usr/bin/python

"""Get all failed boot reports of a job.

The results will include the 'job', 'kernel' and 'board' fields. By default
they will contain also the '_id' field.
"""

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
        "status": "FAIL",
        "field": ["job", "kernel", "board"]
    }

    url = urljoin(BACKEND_URL, "/boot")
    response = requests.get(url, params=params, headers=headers)

    print response.content


if __name__ == "__main__":
    main()
