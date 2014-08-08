Overview
========

Here are described the resources that make up the Kernel CI API.
If you have any problems or suggestions, please report a bug.


Current Version
---------------

Current version of the API is **v1**.

By default all requests receive the **v1** version. In the future, different
versions will have to be explicitly requested using the ``Accept`` header: ::

    Accept: application/v1

HTTP Verbs
----------

Where possible, the API strives to use appropriate HTTP verbs for each action.

Not all the API resources might implement them.

+--------+-------------------------------------+
| Verb   | Description                         |
+========+=====================================+
| GET    | Used to retrieve resources.         |
+--------+-------------------------------------+
| POST   | Used to create or update resources. |
+--------+-------------------------------------+
| DELETE | Used for deleting resources.        |
+--------+-------------------------------------+

.. _http_status_code:

HTTP Response Status Code
-------------------------

All valid response in JSON format will have an HTTP status code of ``200``.
This means that invalid requests may still return an HTTP status code of
``200``.

Queries that do not produce any results, will return a status code of ``200``,
but the JSON response will contain an empty list.

+-------------+--------------------------------------------------------+
| Status Code | Description                                            |
+=============+========================================================+
| 200         | Response is OK.                                        |
+-------------+--------------------------------------------------------+
| 400         | Bad request, more detailed message might be available. |
+-------------+--------------------------------------------------------+
| 403         | Request forbidden.                                     |
+-------------+--------------------------------------------------------+
| 404         | Resource not found.                                    |
+-------------+--------------------------------------------------------+
| 405         | Operation not allowed.                                 |
+-------------+--------------------------------------------------------+
| 420         | JSON not valid or not found.                           |
+-------------+--------------------------------------------------------+
| 500         | Internal error.                                        |
+-------------+--------------------------------------------------------+
| 501         | Method not implemented.                                |
+-------------+--------------------------------------------------------+
| 506         | Wrong response from the database.                      |
+-------------+--------------------------------------------------------+

Schema
------

API access is exclusively over HTTPS and accessed via the
``api.backend.linaro.org`` URL.

Data is sent and received **only** in JSON format.

Results
*******

Query results will always include the ``code`` field reporting the
:ref:`HTTP status code <http_status_code>`. Actual query results
will be included in the ``result`` field and it will always be a list: ::

    {"code": 200, "result": []}

Time and Date
*************

Timestamps are returned as milliseconds since ``January 1, 1970, 00:00:00
UTC`` and are all UTC.

A timestamp will be encoded as follows: ::

    {"created_on": {"$date": 1406788988347}}

Internally, timestamps are stored in `BSON <http://bsonspec.org/>`_ format.

Authentication and Tokens
-------------------------

The only way to authenticate through the API is via an authentication token.
Requests that require authentication will return ``403 Forbidden``.

Authentication is performed using the ``Authorization`` header.

Tokens
******

Tokens should be considered secret data and not exposed to users. To ensure
a higher security, we suggest to use your API token server-side whenever
possible.

Basic Authentication
********************

::

    curl -H 'Authorization: token' https://api.backend.linaro.org
