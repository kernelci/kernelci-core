#!/usr/bin/python

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
        "version": "1.0",
        "lab_name": "lab-name-00",
        "kernel": "next-20141118",
        "job": "next",
        "defconfig": "arm-omap2plus_defconfig",
        "board": "omap4-panda",
        "boot_result": "PASS",
        "boot_time": 10.4,
        "boot_warnings": 1,
        "endian": "little",
        "git_branch": "local/master",
        "git_commit": "fad15b648058ee5ea4b352888afa9030e0092f1b",
        "git_describe": "next-20141118"
    }

    url = urlparse.urljoin(BACKEND_URL, "/boot")
    response = requests.post(url, data=json.dumps(payload), headers=headers)

    print response.content


if __name__ == "__main__":
    main()
