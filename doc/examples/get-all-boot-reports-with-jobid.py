#!/usr/bin/python

"""Get all boot reports with a specified job ID.

The results will include only the 'board', 'status' and 'defconfig' fields.
The '_id' field is explicitly excluded.
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
        "job_id": "123456789012345678901234",
        "field": ["board", "status", "defconfig"],
        "nfield": ["_id"]
    }

    url = urljoin(BACKEND_URL, "/boot")
    response = requests.get(url, params=params, headers=headers)

    print response.content


if __name__ == "__main__":
    main()
