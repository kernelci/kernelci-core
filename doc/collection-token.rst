.. _collection_token:

token
-----

More info about the token schema can be found :ref:`here <schema_token>`.

.. note::
    This resource can also be accessed using the plural form ``tokens``.

.. note::
    All operations on the token resource can only be performed with an administrator
    token.

GET
***

.. http:get:: /token/(string:token)

 Get all the available tokens or a single one if ``token`` is provided.

 :param token: The token whose values to retrieve.
 :type token: string

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
 :query string _id: The internal ID of the token object.
 :query string created_on: The creation date: accepted formats are ``YYYY-MM-DD`` and ``YYYYMMDD``.
 :query string email: The email address associated with the token.
 :query boolean expired: If the token is expired or not.
 :query string username: The user name associated with the token.

 :status 200: Results found.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    GET /token/ HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 .. sourcecode:: http

    GET /token/12345-12345-12345 HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Authorization: token

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Mon, 06 Feb 2015 15:12:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result": [
            {
                "created_on": {
                    "$date": 1407818315043},
                "email": "email@example.net",
                "token": "12345-12345-12345",
                "expired": false
            }
        ]
    }

 .. note::

    Results shown here do not include the full JSON response.

POST
****

.. http:post:: /token

 Create a token as defined in the JSON data.

 For more info on all the required JSON request fields, see the :ref:`JSON token schema for POST requests <schema_token_post>`.

 .. note::
    When creating the first token to be stored in the database, you must use the
    configured master key.

 :reqjson string email: The email associated with the token (**required** only when creating a new token).
 :reqjson string username: The user name associated with the token.
 :reqjson string admin: If the token is an administrator one (it automatically sets GET/DELETE/POST/PUT operations)
 :reqjson string superuser: If the token is a super user one (a super user cannot create new tokens, but can perform GET/DELETE/POST/PUT operations).
 :reqjson boolean get: If the token can perform GET operations.
 :reqjson boolean post: If the token can perform POST/PUT operations.
 :reqjson boolean delete: If the token can perform DELETE operations.
 :reqjson boolean upload: If the token can be used to upload files.
 :reqjson boolean ip_restricted: If the token is restricted to be used on certain IP addresses.
 :reqjson array ip_address: Array of IP addresses the token is restricted to.
 :reqjson boolean lab: If the token is a boot lab one.
 :reqjson boolean test_lab: If the token is a test lab one.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 201: The resource has been created.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http

    POST /token HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "email": "email@example.net",
        "admin": 1,
        "ip_restricted": 1,
        "ip_address": ["192.168.2.1"]
    }

PUT
***

.. http:put:: /token/(string:token_id)

 Update an existing token identified by its ``token_id`` with the values
 provided in the JSON data.

 The ``token_id`` value is different from the token value itself: the ``token_id``
 is the internal ID as provided by the database.

 For more info on all the required JSON request fields, see the :ref:`JSON token schema for POST requests <schema_token_post>`.

 :reqjson string email: The email associated with the token (**required** only when creating a new token).
 :reqjson string username: The user name associated with the token.
 :reqjson string admin: If the token is an administrator one (it automatically sets GET/DELETE/POST/PUT operations)
 :reqjson string superuser: If the token is a super user one (a super user cannot create new tokens, but can perform GET/DELETE/POST/PUT operations).
 :reqjson boolean get: If the token can perform GET operations.
 :reqjson boolean post: If the token can perform POST/PUT operations.
 :reqjson boolean delete: If the token can perform DELETE operations.
 :reqjson boolean upload: If the token can be used to upload files.
 :reqjson boolean ip_restricted: If the token is restricted to be used on certain IP addresses.
 :reqjson array ip_address: Array of IP addresses the token is restricted to.
 :reqjson boolean lab: If the token is a boot lab one.
 :reqjson boolean test_lab: If the token is a test lab one.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: The request has been accepted and the token updated.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http

    POST /token/12345-12345-12345 HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "upload": 1
    }

DELETE
******

.. http:delete:: /token/(string:token_id)

 Delete the token identified by its ``token_id``.

 The ``token_id`` value is different from the token value itself: the ``token_id``
 is the internal ID as provided by the database.

 :param token_id: The token ID as provided by the database.
 :type token_id: string

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: Resource deleted.
 :status 403: Not authorized to perform the operation.
 :status 404: The provided resource has not been found.
 :status 500: Internal database error.

 **Example Requests**

 .. sourcecode:: http

    DELETE /token/abcdefghi HTTP/1.1
    Host: api.kernelci.org
    Accept: */*
    Content-Type: application/json
    Authorization: token

More Info
*********

* :ref:`Token schema <schema_token>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
