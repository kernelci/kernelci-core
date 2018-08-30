.. _collection_test_case:

case
----

More info about the test case schema can be found :ref:`here <schema_test_case>`.

.. note::

    This resource can also be accessed using the plural form ``cases``.

GET
***

.. http:get:: /test/case/(string:id)/

 Get all the available test cases or a single one if ``id`` is provided.

 :param id: The :ref:`ID <intro_schema_ids>` of the test case to retrieve.
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
 :query string _id: The internal ID of the test case report.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string kvm_guest: The name of the KVM guest the test was executed on.
 :query int maximum: The maximum measurement registered.
 :query int minimum: The minimum measurement registered.
 :query string name: The name of a test case.
 :query int samples: Number of registered measurements.
 :query string status: The status of the test execution.
 :query string test_suite_id: The ID of the test suite associated with the test case.
 :query string test_suite_name: The name of the test suite associated with the test case.
 :query string time: The time it took to execute the test case.
 :query string vcs_commit: The VCS commit value.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    GET /test/case HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /tests/cases HTTP/1.1
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
                    "$oid": "123456789",
                    "name": "Test case 0"
                }
            }
        ]
    }

 .. note::
    Results shown here do not include the full JSON response.

POST
****

.. http:post:: /test/case

 Create a new test case as defined in the JSON data. The request will be accepted
 and parsed.

 If saving the test case has success, it will return the associated ID value.

 For more info on all the required JSON request fields, see the :ref:`test case schema for POST requests <schema_test_case_post>`.

 :reqjson string name: The name of the test case.
 :reqjson string test_suite_id: The ID of the test suite the test case belongs to.
 :reqjson string version: The version of the JSON schema format.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 201: The request has been accepted and saved.
 :status 202: The request has been accepted and is going to be created.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    POST /test/case HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "name": "A test case",
        "test_suite_id": "01234567890123456789ABCD",
        "version": "1.0"
    }

 .. sourcecode:: http

    POST /test/case HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "name": "A test case",
        "test_suite_id": "01234567890123456789ABCD",
        "version": "1.0"
    }

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 201 Test case 'A test case' created
    Vary: Accept-Encoding
    Date: Mon, 16 Mar 2014 12:29:51 GMT
    Content-Type: application/json; charset=UTF-8
    Location: /test/case/01234567890123456789ABCD

    {
        "code": 201,
        "result": [
            {
                "_id": {
                    "$oid": "01234567890123456789ABCD"
                }
            }
        ],
        "reason": "Test case 'A test case' created"
    }

PUT
***

.. http:put:: /test/case/(string:id)/

 Update an existing test case identified by its ``id`` with values defined in the JSON data.

 :param id: The :ref:`ID <intro_schema_ids>` of the test case.
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
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http 

    POST /test/case/01234567890123456789ABCD HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "name": "The new name"
    }

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 202 Resource '01234567890123456789ABCD' updated
    Vary: Accept-Encoding
    Date: Mon, 16 Mar 2014 12:29:51 GMT
    Content-Type: application/json; charcase=UTF-8

    {
        "code": 200,
        "reason": "Resource '01234567890123456789ABCD' updated",
    }

DELETE
******

.. http:delete:: /test/case/(string:id)/

 Delete the test case identified by ``id``.

 :param id: The :ref:`ID <intro_schema_ids>` of the test case.
 :type id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: Resource deleted.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal server error.
 :status 503: Service maintenance.

 **Example Requests**

 .. sourcecode:: http

    DELETE /test/case/01234567890123456789ABCD/ HTTP/1.1
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
* :ref:`Test case schema <schema_test_case>`
* :ref:`Test schemas <schema_test>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
