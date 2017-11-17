.. _collection_boot:

boot
----

More info about the boot schema can be found :ref:`here <schema_boot>`.

.. note::

    This resource can also be accessed using the plural form ``boots``.

GET
***

.. http:get:: /boot/(string:id)/

 Get all the available boot reports or a single one if ``id`` is provided.

 :param id: The :ref:`ID <intro_schema_ids>` of the boot report to retrieve.
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
 :query string _id: The internal ID of the boot report.
 :query string board: The name of a board.
 :query string device_type: The name of the device type.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string build_id: The ID of a build document.
 :query string defconfig: The name of a defconfig.
 :query string defconfig_full: The full name of a defconfig (with config fragments).
 :query string endian: The endianness of the board.
 :query string job: The name of a job.
 :query string job_id: The ID of a job.
 :query string kernel: The name of a kernel.
 :query string lab_name: The name of the lab that created the boot report.
 :query string mach: The machine type.
 :query int retries: The number of boot retries performed.
 :query string status: The status of the boot report.
 :query int warnings: The number of warnings in the boot report.
 :query string time_range: Minutes of data to consider, in UTC time
    (:ref:`more info <intro_schema_time_date>`). Minimum value is 10 minutes, maximum
    is 60 * 24.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    GET /boot/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /boot/012345678901234567890123/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /boot?job=next&kernel=next-20140905&field=status&field=defconfig&nfield=_id HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 08 Sep 2014 12:28:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result": [
            {
                "status": "PASS",
                "kernel": "next-20140905",
                "job": "next",
                "_id": "012345678901234567890123",
                "fastboot": false,
                "warnings": 0,
                "defconfig": "arm-omap2plus_defconfig"
            },
        ],
    }

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 08 Sep 2014 12:32:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count": 78,
        "limit": 0,
        "result": [
            {
                "status": "PASS",
                "defconfig": "arm-multi_v7_defconfig"
            },
            {
                "status": "PASS",
                "defconfig": "arm-multi_v7_defconfig"
            },
            {
                "status": "PASS",
                "defconfig": "arm-multi_v7_defconfig+CONFIG_ARM_LPAE=y"
            }
        ],
    }

 .. note::
    Results shown here do not include the full JSON response.

.. http:get:: /boot/distinct/(string:field)/

 Get all the unique values for the specified ``field``.
 Accepted ``field`` values are:

 * `arch`
 * `board_instance`
 * `board`
 * `defconfig_full`
 * `defconfig`
 * `endian`
 * `git_branch`
 * `git_commit`
 * `git_describe`
 * `git_url`
 * `job`
 * `kernel`
 * `lab_name`
 * `mach`

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
 :query string _id: The internal ID of the boot report.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string job: A job name.
 :query string kernel: A kernel name.
 :query string status: The status of the job report.

 :status 200: Results found.
 :status 400: Wrong ``field`` value provided.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    GET /boot/distinct/mach HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /boot/distinct/board?mach=tegra HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Fri, 20 Nov 2015 15:12:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count:" 29,
        "result": [
            "alpine",
            "apm",
            "arm"
        ]
    }

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 11 Aug 2014 15:23:00 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count": 7,
        "result": [
            "tegra124-jetson-tk1",
            "tegra124-jetson-tk1_rootfs:nfs",
            "tegra124-nyan-big"
        ]
    }

 .. note::
    Results shown here do not include the full JSON response.

.. http:get:: /boot/regressions/

 Get the registered boot regressions.

 More info about the boot regressions schema can be found :ref:`here <schema_boot_regressions>`.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :query string field: The field that should be returned in the response. Can be
    repeated multiple times.
 :query string nfield: The field that should *not* be returned in the response. Can be repeated multiple times.
 :query string _id: The internal ID of the registered boot regression.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string job: The name of the job.
 :query string kernel: The name of the kernel.
 :query string job_id: The ID of the job.

 :status 200: Results found.
 :status 400: Wrong values provided.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    GET /boot/regressions?job=next&kernel=next-20160705 HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /boot/regressions?job_id=12345678901234567890ABCD HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

.. http:get:: /boot/(string:id)/regressions/

 Get the registered regressions for the specified boot report.

 This will only return the array with the boot reports that have been tracked
 in the regression.

 More info about the boot regressions schema can be found :ref:`here <schema_boot_regressions>`.

 :param id: The ID of the boot report.
 :type id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: Results found.
 :status 400: Wrong ``id`` value provided.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    GET /boot/12345678901234567890ABCD/regressions/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Tue, 05 Jul 2016 15:12:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count:" 2,
        "result": [
            {
                "_id": {
                    "$oid": "12345678901234567890ABCC"
                },
                "status": "PASS"
            },
            {
                "_id": {
                    "$oid": "12345678901234567890ABCD"
                },
                "status": "FAIL"
            }
        ]
    }

 .. note::
    Results shown here do not include the full JSON response.

.. _collection_boot_post:

POST
****

.. http:post:: /boot

 Create or update a boot report as defined in the JSON data. The request will be accepted and it will begin to parse the available data.

 If the request has been accepted, it will always return ``202`` as the status code.

 For more info on all the required JSON request fields, see the :ref:`boot schema for POST requests <schema_boot_post>`.

 :reqjson string arch: The architecture of the board.
 :reqjson string board: The name of the board.
 :reqjson string defconfig: The name of the defconfig.
 :reqjson string job: The name of the job.
 :reqjson string git_branch: The name of the branch.
 :reqjson string kernel: The name of the kernel.
 :reqjson string lab_name: The name of the boot tests lab.
 :reqjson string version: The version number of the schema.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 202: The request has been accepted and is going to be created.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    POST /boot HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "job": "next",
        "kernel": "next-20140801",
        "defconfig": "all-noconfig",
        "lab_name": "lab-01",
        "board": "beagleboneblack",
        "git_branch": "master"
    }

DELETE
******

.. http:delete:: /boot/(string:id)/

 Delete the boot report identified by ``id``.

 :param id: The :ref:`ID <intro_schema_ids>` of the boot report to delete.
 :type id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :query string _id: The ID of a boot report.
 :query string board: The name of a board.
 :query string defconfig: The name of a defconfig.
 :query string defconfig_full: The full name of a defconfig (with config fragments).
 :query string build_id: The ID of a build document.
 :query string job: The name of a job.
 :query string job_id: The ID of a job.
 :query string kernel: The name of a kernel.
 :query string name: The name of a boot report.

 :status 200: Resource deleted.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    DELETE /boot/01234567890123456789ABCD HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Content-Type: application/json
    Authorization: token

 .. sourcecode:: http

    DELETE /boot?job=mainline&board=legacy,omap3-n900 HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Content-Type: application/json
    Authorization: token


More Info
*********

* :ref:`Boot schema <schema_boot>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
* :ref:`Boot regressions <intro_boot_regressions>`
