.. _collection_test_suite:

suite
-----

More info about the test suite schema can be found :ref:`here <schema_test_suite>`.

.. note::

    This resource can also be accessed using the plural form ``suites``.

GET
***

.. http:get:: /test/suite/(string:id)/

 Get all the available test suites or a single one if ``id`` is provided.

 :param id: The :ref:`ID <intro_schema_ids>` of the test suite to retrieve.
 :type id: string

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
 :query string arch: The platform architecture.
 :query string board: The board where the test suite has been run.
 :query string board_instance: The board instance where the test suite has been run.
 :query string boot_id: The ID of the boot report used by the test suite.
 :query string build_id: The ID of the build report used by the test suite.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string defconfig: A value of the ``defconfig`` used for the build.
 :query string defconfig_full: A value of the ``defconfig_full`` used for the build.
 :query string definition_uri: The URI where the test definition is stored.
 :query string git_branch: The name of the branch.
 :query string job: The tree name.
 :query string job_id: The ID of the job.
 :query string kernel: The kernel name.
 :query string lab_name: The name of the lab executing the test.
 :query string name: The name of a test suite.
 :query string time: The time it took to execute the test set.
 :query string vcs_commit: The VCS commit value.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    GET /test/suite HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /tests/suites HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 16 Mar 2015 14:03:19 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "count": 1,
        "result": [
            {
                "_id": {
                    "$oid": "01234567890123456789ABCD",
                    "name": "Test suite"
                }
            }
        ]
    }

 .. note::
    Results shown here do not include the full JSON response.

POST
****

.. http:post:: /test/suite

 Create a new test suite as defined in the JSON data. The request will be accepted and, if test sets and/or test cases have been specified in the JSON data, it will begin to parse the data.

 If saving the test suite has success, it will return the associated ID value.

 For more info on all the required JSON request fields, see the :ref:`test suite schema for POST requests <schema_test_suite_post>`.

 :reqjson string name: The name of the test suite.
 :reqjson string build_id: The ID of the build report used for testing.
 :reqjson string version: The version of the JSON schema format.

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

    POST /test/suite HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "name": "LSK test suite",
        "build_id": "01234567890123456789ABCD",
        "version": "1.0"
    }

 .. sourcecode:: http

    POST /test/suite HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "name": "LSK test suite",
        "build_id": "01234567890123456789ABCD",
        "version": "1.0",
        "test_case": [
            {
                "name": "Test case 0",
                "version": "1.0"
            }
        ]
    }

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 201 Test suite 'LSK test suite' created
    Vary: Accept-Encoding
    Date: Mon, 16 Mar 2014 12:29:51 GMT
    Content-Type: application/json; charset=UTF-8
    Location: /test/suite/01234567890123456789ABCD

    {
        "code": 201,
        "result": [
            {
                "_id": {
                    "$oid": "01234567890123456789ABCD"
                }
            }
        ],
        "reason": "Test suite 'LSK test suite' created"
    }

 .. sourcecode:: http

    HTTP/1.1 202 Test suite 'LSK test suite' created
    Vary: Accept-Encoding
    Date: Mon, 16 Mar 2014 12:29:51 GMT
    Content-Type: application/json; charset=UTF-8
    Location: /test/suite/01234567890123456789ABCD

    {
        "code": 202,
        "result": [
            {
                "_id": {
                    "$oid": "01234567890123456789ABCD"
                }
            }
        ],
        "reason": "Test suite 'LSK test suite' created",
        "messages": [
            "Test cases will be parsed and imported"
        ]
    }

PUT
***

.. http:put:: /test/suite/(string:id)/

 Update an existing test suite identified by its ``id`` with values defined in the JSON data.

 :param id: The :ref:`ID <intro_schema_ids>` of the test suite.
 :type id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: The resource ahs been updated.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http 

    POST /test/suite/123456789 HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "name": "LSK test suite - NEW",
        "build_id": "01234567890123456789ABCD"
    }

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 202 Resource '123456789' updated
    Vary: Accept-Encoding
    Date: Mon, 16 Mar 2014 12:29:51 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "reason": "Resource '01234567890123456789ABCD' updated",
    }

DELETE
******

.. http:delete:: /test/suite/(string:id)/

 Delete the test suite identified by ``id``. All its associated test sets and test cases will be deleted as well.

 :param id: The :ref:`ID <intro_schema_ids>` of the test suite.
 :type id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: Resource deleted.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    DELETE /test/suite/01234567890123456789ABCD HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Content-Type: application/json
    Authorization: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 202 Resource '01234567890123456789ABCD' deleted
    Vary: Accept-Encoding
    Date: Mon, 16 Mar 2014 12:29:51 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "reason": "Resource '01234567890123456789ABCD' deleted",
    }

More Info
*********

* :ref:`Test suite schema <schema_test_suite>`
* :ref:`Test set schema <schema_test_set>`
* :ref:`Test case schema <schema_test_case>`
* :ref:`Test schemas <schema_test>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
