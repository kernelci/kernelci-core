.. _collection_boot:

boot
----

GET
***

.. http:get:: /boot/(string:boot_id)

 Get all the available boot reports or a single one if ``boot_id`` is provided.

 :param boot_id: The ID of the boot report to retrieve.
 :type boot_id: string

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
 :query string board: The name of a board.
 :query string job: The name of a job.
 :query string job_id: The ID of a job.
 :query string kernel: The name of a kernel.
 :query string defconfig: The name of a defconfig.
 :query string defconfig_id: The ID of a defconfig.
 :query string endian: The endianness of the board.
 :query string board: The name of a board.
 :query string lab_name: The name of the lab that created the boot report.
 :query string name: The name of the boot report.
 :query string status: The status of the boot report.
 :query int warnings: The number of warnings in the boot report.

 :status 200: Resuslts found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    GET /boot/ HTTP/1.1
    Host: api.armcloud.us
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /boot/omap4-panda-next-next-20140905-arm-omap2plus_defconfig HTTP/1.1
    Host: api.armcloud.us
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /boot?job=next&kernel=next-20140905&field=status&field=defconfig&nfield=_id HTTP/1.1
    Host: api.armcloud.us
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
                "_id": "boot-id",
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

.. _collection_boot_post:

POST
****

.. http:post:: /boot

 Create or update a boot report as defined in the JSON data. The request will be accepted and it will begin to parse the available data.

 If the request has been accepted, it will always return ``202`` as the status code.

 For more info on all the required JSON request fields, see the :ref:`boot schema for POST requests <schema_boot_post>`.

 :reqjson string lab_name: The name of the boot tests lab.
 :reqjson string job: The name of the job.
 :reqjson string kernel: The name of the kernel.
 :reqjson string defconfig: The name of the defconfig.
 :reqjson string board: The name of the board.
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

 **Example Requests**

 .. sourcecode:: http 

    POST /boot HTTP/1.1
    Host: api.armcloud.us
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "job": "next",
        "kernel": "next-20140801",
        "defconfig": "all-noconfig",
        "lab_name": "lab-01",
        "board": "beagleboneblack"
    }

DELETE
******

.. http:delete:: /boot/(string:boot_id)

 Delete the boot report identified by ``boot_id``.

 :param boot_id: The ID of the boot report to delete. Usually in the form of: ``board``-``job``-``kernel``-``defconfig``.
 :type boot_id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :query string _id: The ID of a boot report.
 :query string job_id: The ID of a job.
 :query string job: The name of a job.
 :query string kernel: The name of a kernel.
 :query string defconfig_id: The ID of a defconfig.
 :query string defconfig: The name of a defconfig.
 :query string board: The name of a board.
 :query string name: The name of a boot report.

 :status 200: Resource deleted.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    DELETE /boot/tegra30-beaver-next-next-20140612-arm-tegra_defconfig HTTP/1.1
    Host: api.armcloud.us
    Accept: */*
    Content-Type: application/json
    Authorization: token

 .. sourcecode:: http

    DELETE /boot?job=mainline&board=legacy,omap3-n900 HTTP/1.1
    Host: api.armcloud.us
    Accept: */*
    Content-Type: application/json
    Authorization: token


More Info
*********

* :ref:`Boot schema <schema_boot>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
