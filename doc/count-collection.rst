count
-----

GET
***

.. http:get:: /count/(string:collection)

 Count the elements in all collections or in the provided ``collection``.

 :param collection: The collection name to get the count of. Can be one of
    ``job``, ``defconfig``, ``boot``.

 :reqheader X-Linaro-Token: The token necessary to authorize the request.

 :query limit: Number of results to return. Default 0 (all results).
 :type limit: int
 :query skip: Number of results to skip. Default 0 (none).
 :type skip: int
 :query sort: Field to sort the results on. Can be repeated multiple times.
 :query sort_order: The sort order of the results: -1 (descending), 1
    (ascending). This will be applied only to the first ``sort``
    parameter passed. Default -1.
 :type sort_order: int
 :query created_on: Number of days to consider, starting from today. By default
  consider all results.
 :type created_on: int
 :query architecture: The computer architetcture of the result.
 :type architecture: string
 :query board: The name of a board.
 :type board: string
 :query defconfig: A defconfig name.
 :type defconfig: string
 :query job: A job name.
 :type job: string
 :query kernel: A kernel name.
 :type kernel: string

 **Example Requests**

 .. sourcecode:: http

    GET /count/ HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    X-Linaro-Token: token

 .. sourcecode:: http 

    GET /count/job/ HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    X-Linaro-Token: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Wed, 06 Aug 2014 13:08:12 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result": [
            {
                "count": 260,
                "collection": "job"
            }, 
            {
                "count": 32810,
                "collection": "defconfig"
            },
            {
                "count": 10746,
                "collection": "boot"
            }
        ]
    }

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Wed, 06 Aug 2014 13:23:42 GMT

    {
        "code": 200, 
        "result":
        [
            {
                "count": 260,
                "collection": "job"
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
