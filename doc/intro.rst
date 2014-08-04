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

Authentication
--------------

The only way to authenticate through the API is via an authentication token.
Requests that require authentication will return ``403 Forbidden``.

Authentication is performed using the ``X-Linaro-Token`` header.

Basic Authentication
********************

::

    curl -H 'X-Linaro-Token: token' https://api.backend.linaro.org

Schema
------

API access is exclusively over HTTPS and accessed via the
``api.backend.linaro.org`` URL.

Data is sent and received **only** in JSON format.

Time and Date
*************

Timestamps are returned as milliseconds since ``January 1, 1970, 00:00:00
UTC`` and are all UTC.

A timestamp will be encoded as follows: ::

    {"created_on": {"$date": 1406788988347}}

Internally, timestamps are stored in `BSON <http://bsonspec.org/>`_ format.
