version
-------

GET
***

.. http:get:: /version

 Provide the version number of the software running.

 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: Resuslts found.

 .. note::

    This resource does not require authentication.

 **Example Requests**

 .. sourcecode:: http

    GET /version HTTP/1.1
    Host: api.kernelci.org
    Accept: */*

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 24 Nov 2014 18:08:12 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result":
        [
            {
                "version": "2014.11",
                "full_version": "2014.11"
            }
        ]
    }

POST
****

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.


DELETE
******

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.
