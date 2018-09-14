#!/usr/bin/python

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

    test_group = {
        "name": "A test group",
        "build_id": "123456789012345678901234",
        "lab_name": "lab-test-00",
        "test_cases": [
            {
                "name": "A test case - 0"
            },
            {
                "name": "A test case - 1"
            }
        ]
    }

    url = urljoin(BACKEND_URL, "/test/group")
    response = requests.post(url, data=json.dumps(test_group), headers=headers)

    print response.content

if __name__ == "__main__":
    main()
