.. _code_examples:

Code Examples
=============

All the following code examples are Python based and rely on the
`requests <http://docs.python-requests.org/en/latest/>`_ module.

Boot reports examples
---------------------

::

    #!/usr/bin/env python

    """Get all boot reports for a job and a specified kernel."""

    import requests

    from urlparse import urljoin

    BACKEND_URL = 'http://api.armcloud.us'
    AUTHORIZATION_TOKEN = 'foo'
    JOB = 'job'
    KERNEL = 'kernel'


    def main():
        headers = {
            'Authorization': AUTHORIZATION_TOKEN
        }

        params = {
            'job': JOB,
            'kernel': KERNEL
        }

        url = urljoin(BACKEND_URL, '/boot')
        response = requests.get(url, params=params, headers=headers)

        print response.content

    if __name__ == "__main__":
        main()

::

    #!/usr/bin/env python

    """Get all failed boot reports of a job.

    The results will include the'job', 'kernel' and 'board' fields. By default
    they will contain also the '_id' field.
    """

    import requests

    from urlparse import urljoin

    AUTHORIZATION_TOKEN = 'foo'
    BACKEND_URL = 'http://api.armcloud.us'
    JOB = 'job'


    def main():
        headers = {
            'Authorization': AUTHORIZATION_TOKEN
        }

        params = {
            'job': JOB,
            'status': 'FAIL',
            'field': ['job', 'kernel', 'board']
        }

        url = urljoin(BACKEND_URL, '/boot')
        response = requests.get(url, params=params, headers=headers)

        print response.content

    if __name__ == "__main__":
        main()

::

    #!/usr/bin/env python

    """Get all boot reports with a specified job ID.

    The results will include only the 'board', 'status' and 'defconfig' fields.
    The '_id' field is explicitly excluded.
    """

    import requests

    from urlparse import urljoin

    AUTHORIZATION_TOKEN = 'foo'
    BACKEND_URL = 'http://api.armcloud.us'
    JOB = 'job'
    KERNEL = 'kernel'


    def main():
        headers = {
            'Authorization': AUTHORIZATION_TOKEN
        }

        params = {
            'job_id': JOB + '-' + KERNEL,
            'field': ['board', 'status', 'defconfig'],
            'nfield': ['_id']
        }

        url = urljoin(BACKEND_URL, '/boot')
        response = requests.get(url, params=params, headers=headers)

        print response.content

    if __name__ == "__main__":
        main()

Handling compressed data
------------------------

If you need to directly handle the compressed data as returned by the server,
you can access it from the response object.

Keep in mind though that the `requests <http://docs.python-requests.org/en/latest/>`_
module automatically handles ``gzip`` and ``deflate`` compressions.

::

    #!/usr/bin/env python

    """Get all defconfig reports with a specified job ID.

    Explicitly defines the Accept-Encoding header and manually handle the
    compressed data.
    """

    import gzip
    import requests

    from cStringIO import StringIO
    from urlparse import urljoin

    AUTHORIZATION_TOKEN = 'foo'
    BACKEND_URL = 'http://api.armcloud.us'
    JOB = 'job'
    KERNEL = 'kernel'


    def main():
        headers = {
            'Authorization': AUTHORIZATION_TOKEN,
            'Accept-Encoding': 'gzip'
        }

        params = {
            'job_id': JOB + '-' + KERNEL,
        }

        url = urljoin(BACKEND_URL, '/defconfig')
        response = requests.get(url, params=params, headers=headers, stream=True)

        in_buffer = StringIO(response.raw.data)
        json_str = ""

        with gzip.GzipFile(mode='rb', fileobj=in_buffer) as g_data:
            json_str = g_data.read()

        print json_str

    if __name__ == "__main__":
        main()
