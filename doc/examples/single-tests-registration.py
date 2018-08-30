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

    test_suite = {
        "name": "A test suite",
        "build_id": "123456789012345678901234",
        "lab_name": "lab-test-00"
    }

    url = urljoin(BACKEND_URL, "/test/suite")
    response = requests.post(url, data=json.dumps(test_suite), headers=headers)

    if response.status_code == 201:
        test_suite_result = response.json()["result"][0]
        test_suite_id = test_suite_result["_id"]["$oid"]

        test_case = {
            "name": "A test case",
            "test_suite_id": test_suite_id
        }


        url = urljoin(BACKEND_URL, "/test/case")
        response = requests.post(
            url, data=json.dumps(test_case), headers=headers)

        print response.content

if __name__ == "__main__":
    main()
