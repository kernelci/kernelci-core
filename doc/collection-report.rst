.. _collection_report:

report
------

A **report** is the result of sending a boot or build report. The actual report sent is not stored here, only information on the report status are.

More info about the report schema can be found :ref:`here <schema_report>`.

.. note::

    This resource can only be accessed with an admin or super user token.

.. note::

    This resource can also be accessed using the plural form ``reports``.

GET
***

.. http:get:: /report/(string:id)

 Get all the available reports or a single one if ``id`` is provided.

 :param id: The ID of the report to retrieve.
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
 :query string _id: The internal ID of the report.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string job: A job name.
 :query string kernel: A kernel name.
 :query string name: The name of the report.
 :query string status: The status of the report report.
 :query string type: The type of the report.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    GET /report/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /report/?job=next&kernel=next-20140731 HTTP/1.1
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
        "count:" 1,
        "limit": 0,
        "result": [
            {
                "status": "SENT",
                "job": "next",
                "kernel": "next-20140731",
            },
        ],
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

More Info
*********

* :ref:`Report schema <schema_report>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
