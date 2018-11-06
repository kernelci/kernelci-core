#!/usr/bin/python

"""Get all build reports with a specified job ID.

Explicitly defines the Accept-Encoding header and manually handle the
compressed data.
"""

import gzip
import requests

from cStringIO import StringIO
from urlparse import urljoin

BACKEND_URL = "https://api.kernelci.org"
AUTHORIZATION_TOKEN = "foo"


def main():
    headers = {
        "Authorization": AUTHORIZATION_TOKEN,
        "Accept-Encoding": "gzip"
    }

    params = {
        "job_id": "123456789012345678901234",
    }

    url = urljoin(BACKEND_URL, "/build")
    response = requests.get(url, params=params, headers=headers, stream=True)

    in_buffer = StringIO(response.raw.data)
    json_str = ""

    with gzip.GzipFile(mode="rb", fileobj=in_buffer) as g_data:
        json_str = g_data.read()

    print json_str


if __name__ == "__main__":
    main()
