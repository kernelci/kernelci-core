.. _collection_batch:

batch
-----

The batch resource is used to perform a series of operations in batch: if you
have more than one request to perform, instead of sending each request on its
own, send a single batch operation request specifying all your requests.

It works by receiving a ``POST`` request with the operations to perform.

.. note::

    At the moment the batch operator can perform only GET operations on
    the available resources.

GET
***

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.

POST
****

.. http:post:: /batch

 Perform the specified batch operations.

 :reqjson array batch: The default batch operator; it is a list of objects
    made of the keywords described below.
 :reqjsonarr string method: The method of the request. Only ``GET`` is
    supported.
 :reqjsonarr string operation_id: An identification for this request opearation.
 :reqjsonarr string resource: On which resource the request should be
    performed.
 :reqjsonarr string document: The ID of a document in the specified resource.
    For the ``count`` resource, this is used to identify the actual resource to
    perform the count on.
 :reqjsonarr string query: The query to perform as a series of ``key=value``
    pairs separated by the ampersand ("&") character. The keys must be
    the same specified in each resources query parameters.
 :resjsonarr int code: The HTTP code of the response.
 :resjsonarr array result: The list of result objects for each operation in the
    batch. If the ``operation_id`` parameter was specified, it will be included
    in each object. Each ``result`` object in turn contains another ``result``
    array that holds the query results.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: The request has been accepted and created.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http 

    POST /batch HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "batch": [
            {
                "method": "GET",
                "operation_id": "op-0",
                "resource": "count",
                "document": "boot",
                "query": "status=FAIL&job=next&date_range=5"
            },
            {
                "method": "GET",
                "operation_id": "op-1",
                "resource": "defconfig",
                "query": "status=PASS&job=mainline&date_range=5&field=arch&field=defconfig"
            },
            {
                "method": "GET",
                "operation_id": "op-2",
                "resource": "boot",
                "document": "123456789012345678901234"
            }
        ]
    }

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 20 Oct 2014 11:33:24 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result": [
            {
                "operation_id": "op-0",
                "result": [
                    {
                        "count": 5,
                        "resource": "boot"
                    }
                ]
            },
            {
                "operation_id": "op-1",
                "result": [
                    {
                        "arch": "arm64",
                        "defconfig": "bcm2835_defconfig",
                        "_id": "baz"
                    }
                ]
            },
            {
                "operation_id": "op-2",
                "result": [
                    {
                        "arch": "arm"
                    }
                ]
            }
        ]
    }

PUT
***

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.

DELETE
******

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.
