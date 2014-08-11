job
---

GET
***

.. http:get:: /job/(string:job_id)

 Get all the available jobs or a single one if ``job_id`` is provided.

 :param job_id: The ID of the job to retrieve in the form of ``job``-``kernel``.
 :type job_id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :query limit: Number of results to return. Default 0 (all results).
 :type limit: int
 :query skip: Number of results to skip. Default 0 (none).
 :type skip: int
 :query sort: Field to sort the results on. Can be repeated multiple times.
 :query sort_order: The sort order of the results: -1 (descending), 1
    (ascending). This will be applied only to the first ``sort``
    parameter passed. Default -1.
 :type sort_order: int
 :query date_range: Number of days to consider, starting from today
    (:ref:`more info <schema_time_date>`). By default consider all results.
 :type date_range: int
 :query field: The field that should be returned in the response. Can be
    repeated multiple times.
 :type field: string
 :query job: A job name.
 :type job: string
 :query kernel: A kernel name.
 :type kernel: string

 **Example Requests**

 .. sourcecode:: http

    GET /job/ HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /job/next-next-20140731 HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /job?date_range=12&job=arm-soc&filed=status&field=kernel HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    Authorization: token    

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 11 Aug 2014 15:12:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count:" 261,
        "limit": 0,
        "result": [
            {
                "status": "PASS",
                "job": "arm-soc",
                "_id": "arm-soc-v3.15-8898-gf79922c",
            },
        ],
    }

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 11 Aug 2014 15:23:00 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": "200",
        "result": [
            {
                "status": "PASS",
                "job": "next",
                "_id": "next-next-20140731",
                "kernel": "next-20140731"
            }
        ]
    }

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 11 Aug 2014 15:23:00 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count": 4,
        "limit": 0,
        "result": [
            {
                "status": "PASS",
                "kernel": "v3.16-rc6-1009-g709032a"
            }, 
            {
                "status": "PASS",
                "kernel": "v3.16-rc6-1014-g716519f"
            }
        ]
    }

 .. note::
    Results shown here do not include the full JSON response.

POST
****

DELETE
******
