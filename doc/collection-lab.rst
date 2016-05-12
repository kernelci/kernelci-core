.. _collection_lab:

lab
---

More info about the lab schema can be found :ref:`here <schema_lab>`.

.. note::

    This resource can also be accessed using the plural form ``labs``.

GET
***

.. http:get:: /lab/(string:id)/

 Get all the available registered lab or a single one if ``id`` is
 provided.

 :param id: The :ref:`ID <intro_schema_ids>` of the lab to retrieve.
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
 :query string _id: The internal ID of the registered lab.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string name: The name of the lab.
 :query boolean private: If the lab is private or not.
 :query string token: The ID of the token associated with the lab.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    GET /lab/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /boot/lab-01 HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Tue, 10 Nov 2014 12:28:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result": [
            {
                "name": "lab-01",
                "private": false,
                "address": {
                    "street_1": "Example street"
                },
                "contact": {
                    "name": "Name",
                    "surname": "Surname",
                    "email": "example@example.net"
                }
            },
        ],
    }

 .. note::
    Results shown here do not include the full JSON response.

POST
****

.. http:post:: /lab

 Create a new lab document as defined in the JSON data.

 For more info on all the required JSON request fields, see the :ref:`lab
 schema <schema_lab_post>`.

 :reqjson string name: The name that should be given to the lab.
 :reqjson object contact: The contact data associated with the lab.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 201: The request has been accepted and the lab created.
 :status 400: JSON data not valid, or provided name for the lab already exists.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http 

    POST /lab HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "name": "lab-01",
        "contact": {
            "name": "Name",
            "surname": "Surname",
            "email": "example@example.net"
        }
    }

PUT
***

.. http:put:: /lab/(string:id)

 Update an existing lab document identified by the ``id`` value.

 For more info on all the required JSON request fields, see the :ref:`lab
 schema <schema_lab_post>`.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: The request has been accepted and the lab updated.
 :status 400: JSON data not valid, or provided name for the lab already exists.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http 

    PUT /lab/0123456789ab0123456789ab HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "name": "update-lab-name",
    }

DELETE
******

.. http:delete:: /lab/(string:id)

 Delete the lab document identified by the ``id`` value.

 :param id: The :ref:`ID <intro_schema_ids>` of the lab document to delete.
 :type id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :query string _id: The internal ID of the registered lab.
 :query string private: If the lab is private or not.
 :query string token: The ID of token associated with the lab.

 :status 200: Resource deleted.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    DELETE /lab/0123456789ab0123456789ab HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Content-Type: application/json
    Authorization: token


More Info
*********

* :ref:`Lab schema <schema_lab>`
* :ref:`API results <intro_schema_results>`
