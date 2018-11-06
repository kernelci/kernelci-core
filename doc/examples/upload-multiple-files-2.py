#!/usr/bin/python

import io
import requests

from requests_toolbelt import MultipartEncoder
from urlparse import urljoin

BACKEND_URL = "https://api.kernelci.org"
AUTHORIZATION_TOKEN = "foo"


def main():
    data = MultipartEncoder(
        fields={
            "path": "next/next-20150116/arm64-allnoconfig/",
            "file1": ("Image", io.open("/path/to/Image", mode="rb")),
            "file2": ("kernel.config", io.open("/path/to/kernel.config", mode="rb")),
            "file3": ("build.json", io.open("/path/to/build.json", mode="rb")),
            "file4": ("build.log", io.open("/path/to/build.log", mode="rb")),
            "file5": ("System.map", io.open("/path/to/System.map", mode="rb")),
        }
    )

    headers = {
        "Authorization": AUTHORIZATION_TOKEN,
        "Content-Type": data.content_type
    }

    url = urljoin(BACKEND_URL, "/upload")
    response = requests.post(url, headers=headers, data=data)

    print response.content


if __name__ == "__main__":
    main()
