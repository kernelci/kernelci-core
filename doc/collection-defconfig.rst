.. _collection_defconfig:

defconfig
---------

More info about the defconfig schema can be found :ref:`here <schema_defconfig>`.

.. note::

    This resource can also be accessed using the plural form ``defconfigs``.

GET
***

.. http:get:: /defconfig/(string:defconfig_id)

 Get all the available defconfigs built or a single one if ``defconfig_id`` is provided.

 :param defconfig_id: The ID of the defconfig to retrieve.
 :type defconfig_id: string

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
 :query string field: The field that should be returned in the response. Can be
    repeated multiple times.
 :query string nfield: The field that should *not* be returned in the response. Can be repeated multiple times.
 :query string _id: The internal ID of the defconfig report.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string job: The name of a job.
 :query string job_id: The ID of a job.
 :query string kernel: The name of a kernel.
 :query string defconfig_full: The full name of a defconfig (with config fragments).
 :query string defconfig: The name of a defconfig.
 :query string arch: The architecture on which the defconfig has been built.
 :query string status: The status of the defconfig report.
 :query int warnings: The number of warnings in the defconfig built.
 :query int errors: The number of errors in the defconfig built.
 :query string git_branch: The name of the git branch.
 :query string git_commit: The git commit SHA.
 :query string git_describe: The git describe value.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    GET /defconfig/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /defconfig/next-next-20140905-arm-omap2plus_defconfig HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /defconfig?job=next&kernel=next-20140905&field=status&field=arch&nfield=_id HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 **Examples Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 08 Sep 2014 14:16:52 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result": [
            {
                "status": "PASS",
                "kernel": "next-20140905",
                "dirname": "arm-omap2plus_defconfig",
                "job_id": "next-next-20140905",
                "job": "next",
                "defconfig": "omap2plus_defconfig",
                "errors": null,
                "_id": "next-next-20140905-arm-omap2plus_defconfig",
                "arch": "arm",
            }
        ]
    }

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 08 Sep 2014 14:20:52 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count": 132,
        "limit": 0,
        "result": [
            {
                "status": "PASS",
                "arch": "arm"
            },
            {
                "status": "PASS",
                "arch": "arm"
            },
            {
                "status": "PASS",
                "arch": "x86"
            },
            {
                "status": "PASS",
                "arch": "arm64"
            }
        ]
    }

 .. note::
    Results shown here do not include the full JSON response.

.. http:get:: /defconfig/(string:defconfig_id)/logs/
.. http:get:: /defconfig/logs/

 Get the redacted logs of the built defconfig. The redacted logs contain only
 the warning, error and mismatched lines from the build log.

 For more info about the available fields, see the :ref:`defconfig logs schema <schema_defconfig_logs>`

 :param defconfig_id: The ID of the defconfig to retrieve.
 :type defconfig_id: string

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
 :query string field: The field that should be returned in the response. Can be
    repeated multiple times.
 :query string nfield: The field that should *not* be returned in the response. Can be repeated multiple times.
 :query string _id: The internal ID of the defconfig logs report.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string job: The name of a job.
 :query string job_id: The ID of a job.
 :query string kernel: The name of a kernel.
 :query string defconfig_full: The full name of a defconfig (with config fragments).
 :query string defconfig: The name of a defconfig.
 :query string arch: The architecture on which the defconfig has been built.
 :query string status: The status of the defconfig report.
 :query int warnings_count: The number of warnings in the defconfig build log.
 :query int errors_count: The number of errors in the defconfig build log.
 :query int mismatches_count: The number of mismatched lines in the defconfig build log.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    GET /defconfig/123456789012345678901234/logs/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /defconfig/logs?job=next&kernel=next-20150709&defconfig=omap2plus_defconfig HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

POST
****

.. http:post:: /defconfig

 Parse a single defconfig built from the provided data. The request will be accepted and it will begin to parse the data.

 Before issuing a POST request on the defconfig resource, the data must have been uploaded
 to the server. This resource is used to trigger the parsing of the data directly on the server.

 For more info on all the required JSON data fields, see the :ref:`defconfig schema for POST requests <schema_defconfig_post>`.

 :reqjson string job: The name of the job.
 :reqjson string kernel: The name of the kernel.
 :reqjson string defconfig: The name of the defconfig built.
 :reqjson string arch: The architecture type.
 :reqjson string defconfig_full: The full name of the defconfig (optional). Necessary if the defconfig built contained config fragments or other values.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 202: The request has been accepted and the resource will be created.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http 

    POST /defconfig HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "job": "next",
        "kernel": "next-20140706",
        "defconfig": "tinyconfig",
        "arch": "x86"
    }

 .. sourcecode:: http 

    POST /defconfig HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "job": "next",
        "kernel": "next-20140706",
        "defconfig": "multi_v7_defconfig",
        "defconfig_full": "multi_v7_defconfig+CONFIG_CPU_BIG_ENDIAN=y",
        "arch": "arm"
    }

DELETE
******

.. http:delete:: /defconfig/(string:defconfig_id)

 Delete the job identified by ``defconfig_id``.

 :param defconfig_id: The ID of the defconfig to retrieve. Usually in the form of: ``job``-``kernel``-``defconfig``.
 :type defconfig_id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: Resource deleted.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 422: No real JSON data provided.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    DELETE /defconfig/next-next-20140905-arm-omap2plus_defconfig HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Content-Type: application/json
    Authorization: token

More Info
*********

* :ref:`Defconfig schema <schema_defconfig>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
