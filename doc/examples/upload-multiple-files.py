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

    data = {
        "path": "next/next-20150116/arm64-allnoconfig/"
    }

    files = [
        ("file1", ("Image", io.open("/path/to/Image", mode="rb"))),
        ("file2", ("kernel.config", io.open("/path/to/kernel.config", mode="rb"))),
        ("file3", ("build.json", io.open("/path/to/build.json", mode="rb"))),
        ("file4", ("build.log", io.open("/path/to/build.log", mode="rb"))),
        ("file5", ("System.map", io.open("/path/to/System.map", mode="rb"))),
    ]

    url = urljoin(BACKEND_URL, "/upload")
    response = requests.post(url, data=data, headers=headers, files=files)

    print response.content


if __name__ == "__main__":
    main()
