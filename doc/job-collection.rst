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

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :query int limit: Number of results to return. Default 0 (all results).
 :query int skip: Number of results to skip. Default 0 (none).
 :query string sort: Field to sort the results on. Can be repeated multiple times.
 :query int sort_order: The sort order of the results: -1 (descending), 1
    (ascending). This will be applied only to the first ``sort``
    parameter passed. Default -1.
 :query int date_range: Number of days to consider, starting from today
    (:ref:`more info <schema_time_date>`). By default consider all results.
 :query string field: The field that should be returned in the response. Can be
    repeated multiple times.
 :query string job: A job name.
 :query string kernel: A kernel name.

 :status 200: Resuslts found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

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

.. http:post:: /job

 Create or update a job as defined in the JSON data. The request will be accepted and it will begin to parse the data.

 :reqjson string job: The name of the job.
 :reqjson string kernel: The name of the kernel.

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

    POST /api/job HTTP/1.1
    Host: api.backend.linaro.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "job": "next",
        "kernel": "next-20140801"
    }

DELETE
******

.. http:delete:: /job/job_id

 Delete the job identified by ``job_id``.

 :param job_id: The job ID in the form of ``job``-``kernel``.
 :type job_id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: Resource deleted.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    DELETE /job/next-next-20140612 HTTP/1.1
    Host: api.backend.linaro.org
    Accept: */*
    Content-Type: application/json
    Authorization: token
