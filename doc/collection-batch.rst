.. _collection_batch:

batch
-----

This is not a real collection. It is instead used to perform a series of operations in batch: if you have more than one request to perform, instead of
sending each request on its own, send a single batch operation request
specifying all your requests.

It works by receiving a ``POST`` request with the operations to perform.

.. note::

    At the moment the batch operator can perform only GET operations on
    the available collections.

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
 :reqjsonarr string collection: On which collection the request should be
    performed.
 :reqjsonarr string document_id: The ID of a document in the collection. For
    the ``count`` collection, this is used to identify on which collection to
    perform the count.
 :reqjsonarr string query: The query to perform as a series of ``key=value``
    pairs separated by the ampersand ("&") character. The keys must be
    the same specified in each collections query parameters.
 :resjsonarr int code: The HTTP code of the response.
 :resjsonarr array result: The list of result objects for each operation in the
    batch. If the ``operation_id`` parameter was specified, it will be included
    in each object. Each ``result`` object in turn contains another ``result``
    array that holds the query results.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 202: The request has been accepted and is going to be created.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http 

    POST /batch HTTP/1.1
    Host: api.armcloud.us
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "batch": [
            {
                "method": "GET",
                "operation_id": "foo",
                "collection": "count",
                "document_id": "boot",
                "query": "status=FAIL&job=next&date_range=5"
            },
            {
                "method": "GET",
                "operation_id": "bar",
                "collection": "defconfig",
                "query": "status=PASS&job=mainline&date_range=5&field=arch&field=defconfig"
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
                "operation_id": "foo",
                "result": [
                    {
                        "count": 5,
                        "collection": "boot"
                    }
                ]
            },
            {
                "operation_id": "bar",
                "result": [
                    {
                        "arch": "arm64",
                        "defconfig": "bcm2835_defconfig",
                        "_id": "baz"
                    }
                ]
            }
        ]
    }

DELETE
******

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.
