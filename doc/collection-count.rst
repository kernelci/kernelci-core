count
-----

GET
***

.. http:get:: /count/(string:resource)/

 Count the elements in all resources or in the provided ``resource``.

 :param resource: The name of the resource to get the count of.
    Can be one of ``boot``, ``defconfig``, ``job``.
 :type resource: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :query int limit: Number of results to return. Default 0 (all results).
 :query int skip: Number of results to skip. Default 0 (none).
 :query string sort: Field to sort the results on. Can be repeated multiple times.
 :query int sort_order: The sort order of the results: -1 (descending), 1
    (ascending). This will be applied only to the first ``sort``
    parameter passed. Default -1.
 :query int date_range: Number of days to consider, starting from today
    (:ref:`more info <intro_schema_time_date>`). By default consider all results.
 :query string arch: A type of computer architecture (like ``arm``, ``arm64``).
 :query string board: The name of a board.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string defconfig: A defconfig name.
 :query int errors: The number of errors.
 :query string job: A job name.
 :query string job_id: A job ID.
 :query string kernel: A kernel name.
 :query boolean private: The private status.
 :query string status: The status of the elements to get the count of. Can be
    one of: ``PASS`` or ``FAIL``.
 :query int warnings: The number of warnings.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 .. note::

    Not all the query parameters are valid for each resource. Please refer
    to the GET method :ref:`documentation <collections>` of the resource to
    know which parameters can be used.

 **Example Requests**

 .. sourcecode:: http

    GET /count/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http 

    GET /count/job/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /count/job?job=next&date_range=1 HTTP/1.1
    Host: api.kernelci.org
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
