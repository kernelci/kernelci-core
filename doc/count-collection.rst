count
-----

GET
***

.. http:get:: /count/(string:collection)

 Count the elements in all collections or in the provided ``collection``.

 When using the query parameters, the results will include also the fields
 specified.

 :param collection: The name of the collection to get the count of.
    Can be one of ``job``, ``defconfig``, ``boot``.

 :reqheader Authorization: The token necessary to authorize the request.

 :query limit: Number of results to return. Default 0 (all results).
 :type limit: int
 :query skip: Number of results to skip. Default 0 (none).
 :type skip: int
 :query sort: Field to sort the results on. Can be repeated multiple times.
 :query sort_order: The sort order of the results: -1 (descending), 1
    (ascending). This will be applied only to the first ``sort``
    parameter passed. Default -1.
 :type sort_order: int
 :query created_on: Number of days to consider, starting from today
    (:ref:`more info <schema_time_date>`). By default consider all results.
 :type created_on: int
 :query arch: A type of computer architetcture (like ``arm``, ``arm64``).
 :type arch: string
 :query board: The name of a board.
 :type board: string
 :query defconfig: A defconfig name.
 :type defconfig: string
 :query job: A job name.
 :type job: string
 :query job_id: A job ID (usually in the form of ``job``-``kernel``).
 :type job_id: string
 :query kernel: A kernel name.
 :type kernel: string

 **Example Requests**

 .. sourcecode:: http

    GET /count/ HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http 

    GET /count/job/ HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /count/job?job=next&date_range=1 HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    Authorization: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Wed, 06 Aug 2014 13:08:12 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result":
        [
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

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Fri, 08 Aug 2014 14:15:40 GMT

    {
        "code": 200,
        "result":
        [
            {
                "count": 1,
                "collection": "job",
                "fields": {
                    "job": "next",
                    "created_on": {
                        "$lt": {
                            "$date": 1407542399000
                        },
                        "$gte": {
                            "$date": 1407369600000
                        }
                    }
                }
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
