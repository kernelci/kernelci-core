#!/usr/bin/python

import io
import requests

from urlparse import urljoin

BACKEND_URL = "https://api.kernelci.org"
AUTHORIZATION_TOKEN = "foo"


def main():
    headers = {
        "Authorization": AUTHORIZATION_TOKEN
    }

    url = urljoin(
        BACKEND_URL,
        "/upload/next/next-20150116/arm64-allnoconfig/lab-name/boot-arch.json")

    with io.open("/path/to/boot-arch.json", mode="rb") as upload_file:
        response = requests.put(url, headers=headers, data=upload_file)

    print response.content


if __name__ == "__main__":
    main()
