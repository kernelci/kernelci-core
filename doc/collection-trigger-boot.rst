.. _collection_trigger_boot:

boot
----

The boot trigger resource is used by a boot ``lab`` to retrieve ``build``
information on what can be boot tested.

The data returned by this resources has the same format described in the :ref:`build schema <schema_build>`.

By default, this resource returns the same results as the ``build`` one. The
results can be tailored for the requesting lab by comparing what other boot
labs have already tested. To achieve this, use the ``compared`` parameter in
the query string.

.. note::

    This resource can also be accessed using the plural form ``boots``.

.. note::

    This resource can only be accessed by a lab token.

GET
***

.. http:get:: /trigger/boot

 Get the available builds.

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
 :query int compared: If the search results should be compared against already available boot reports.
 :query string job: The name of a job.
 :query string job_id: The ID of a job.
 :query string kernel: The name of a kernel.
 :query string defconfig_full: The full name of a defconfig (with config fragments).
 :query string defconfig: The name of a defconfig.
 :query string arch: The architecture on which the defconfig has been built.
 :query string status: The status of the defconfig report.
 :query string git_branch: The name of the git branch.
 :query string git_commit: The git commit SHA.
 :query string git_describe: The git describe value.
 :query string time_range: Minutes of data to consider, in UTC time
    (:ref:`more info <intro_schema_time_date>`). Minimum value is 10 minutes, maximum
    is 60 * 24.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    GET /trigger/boot HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /trigger/boot?job=next&date_range=1 HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /trigger/boot?job=next&kernel=next-20140905&compared=1 HTTP/1.1
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
                "job_id": "123456789012345678901",
                "job": "next",
                "defconfig": "omap2plus_defconfig",
                "_id": "12345678901234567890",
                "arch": "arm",
            }
        ]
    }

 .. note::
    Results shown here do not include the full JSON response.

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

PUT
***

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.


More Info
*********

* :ref:`Defconfig schema <schema_build>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
