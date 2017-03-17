.. _collection_build:

build
-----

More info about the build schema can be found :ref:`here <schema_build>`.

.. note::

    This resource can also be accessed using the plural form ``builds``.

GET
***

.. http:get:: /build/(string:id)/

 Get all the available builds built or a single one if ``id`` is provided.

 :param id: The :ref:`ID <intro_schema_ids>` of the build to retrieve.
 :type id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :query int limit: Number of results to return. Default 0 (all results).
 :query int skip: Number of results to skip. Default 0 (none).
 :query string sort: Field to sort the results on. Can be repeated multiple times.
 :query int sort_order: The sort order of the results: -1 (descending), 1
    (ascending). This will be applied only to the first ``sort``
    parameter passed. Defaults to -1.
 :query int date_range: Number of days to consider, starting from today
    (:ref:`more info <intro_schema_time_date>`). By default consider all results.
 :query string field: The field that should be returned in the response. Can be
    repeated multiple times.
 :query string nfield: The field that should *not* be returned in the response. Can be repeated multiple times.
 :query string _id: The internal ID of the build report.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string arch: The architecture on which it was built.
 :query string build_type: The type of the build.
 :query string defconfig: The name of a defconfig.
 :query string defconfig_full: The full name of a defconfig (with config fragments).
 :query int errors: The number of errors found in the build log.
 :query string git_branch: The name of the git branch.
 :query string git_commit: The git commit SHA.
 :query string git_describe: The git describe value.
 :query string job: The name of a job.
 :query string job_id: The ID of a job.
 :query string kernel: The name of a kernel.
 :query string status: The status of the build report.
 :query string time_range: Minutes of data to consider, in UTC time
    (:ref:`more info <intro_schema_time_date>`). Minimum value is 10 minutes, maximum
    is 60 * 24.
 :query int warnings: The number of warnings found in the build log.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    GET /build/012345678901234567890123/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /build?job=next&kernel=next-20140905&field=status&field=arch&nfield=_id HTTP/1.1
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
                "job_id": "012345678901234567890123",
                "job": "next",
                "defconfig": "omap2plus_defconfig",
                "errors": null,
                "_id": "012345678901234567890123",
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

.. http:get:: /build/distinct/(string:field)

 Get all the unique values for the specified ``field``.
 Accepted ``field`` values are:

 * `arch`
 * `compiler_version_ext`
 * `compiler_version`
 * `compiler`
 * `defconfig_full`
 * `defconfig`
 * `git_branch`
 * `git_commit`
 * `git_describe_v`
 * `git_describe`
 * `git_url`
 * `job`
 * `kernel_version`
 * `kernel`

 The query parameters can be used to first filter the data on which the unique
 value should be retrieved.

 :param field: The name of the field to get the unique values of.
 :type field: string

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
 :query string _id: The internal ID of the build report.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string job: A job name.
 :query string kernel: A kernel name.
 :query string status: The status of the build report.

 :status 200: Results found.
 :status 400: Wrong ``field`` value provided.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    GET /build/distinct/arch HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /build/distinct/kernel?job=next&date_range=5 HTTP/1.1
    Host: api.kernelci.org
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
        "count:" 4,
        "result": [
            "arm",
            "arm64",
            "x86",
            "x86_64"
        ]
    }

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 11 Aug 2014 15:23:00 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count": 2,
        "result": [
            "next-20150826",
            "next-20150825",
        ]
    }

 .. note::
    Results shown here do not include the full JSON response.

.. http:get:: /build/(string:build_id)/logs/
.. http:get:: /build/logs/

 Get the redacted logs of the build. The redacted logs contain only
 the warning, error and mismatched lines from the build log.

 For more info about the available fields, see the :ref:`build logs schema <schema_build_logs>`

 :param build_id: The ID of the build.
 :type build_id: string

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
 :query string _id: The internal ID of the build logs report.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string job: The name of a job.
 :query string job_id: The ID of a job.
 :query string kernel: The name of a kernel.
 :query string defconfig_full: The full name of a defconfig (with config fragments).
 :query string defconfig: The name of a defconfig.
 :query string arch: The architecture on which it has been built.
 :query string status: The status of the build.
 :query int warnings: The number of warnings in the build log.
 :query int errors: The number of errors in the build log.
 :query int mismatches: The number of mismatched lines in the build log.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    GET /build/123456789012345678901234/logs/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /build/logs?job=next&kernel=next-20150709&defconfig=omap2plus_defconfig HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

POST
****

.. http:post:: /build

 Parse a single build result. The request will be accepted and it will begin to parse the data.

 Before issuing a POST request on the build resource, the data must have been uploaded
 to the server. This resource is used to trigger the parsing of the data.

 For more info on all the required JSON data fields, see the :ref:`build schema for POST requests <schema_build_post>`.

 :reqjson string job: The name of the job.
 :reqjson string kernel: The name of the kernel.
 :reqjson string defconfig: The name of the defconfig built.
 :reqjson string arch: The architecture type.
 :reqjson string defconfig_full: The full name of the defconfig (optional). Necessary if the defconfig built contained configuration fragments or other values.
 :reqjson string git_branch: The name of the branch.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 202: The request has been accepted and the resource will be created.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http 

    POST /build HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "job": "next",
        "kernel": "next-20140706",
        "defconfig": "tinyconfig",
        "arch": "x86",
        "git_branch": "master"
    }

 .. sourcecode:: http 

    POST /build HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "job": "next",
        "kernel": "next-20140706",
        "defconfig": "multi_v7_defconfig",
        "defconfig_full": "multi_v7_defconfig+CONFIG_CPU_BIG_ENDIAN=y",
        "arch": "arm",
        "git_branch": "master"
    }

DELETE
******

.. http:delete:: /build/(string:id)/

 Delete the build identified by ``id``.

 :param id: The :ref:`ID <intro_schema_ids>` of the build to delete.
 :type id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: Resource deleted.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 422: No real JSON data provided.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    DELETE /build/01234567890123456789ABCD HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Content-Type: application/json
    Authorization: token

More Info
*********

* :ref:`Build schema <schema_build>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
