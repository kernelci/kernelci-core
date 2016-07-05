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

+------------+-------------------------------------+
| Verb       | Description                         |
+============+=====================================+
| GET        | Used to retrieve resources.         |
+------------+-------------------------------------+
| POST/PUT   | Used to create or update resources. |
+------------+-------------------------------------+
| DELETE     | Used for deleting resources.        |
+------------+-------------------------------------+

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
| 201         | Resource created.                                      |
+-------------+--------------------------------------------------------+
| 202         | Request accepted.                                      |
+-------------+--------------------------------------------------------+
| 400         | Bad request, more detailed message might be available. |
+-------------+--------------------------------------------------------+
| 403         | Request forbidden.                                     |
+-------------+--------------------------------------------------------+
| 404         | Resource not found.                                    |
+-------------+--------------------------------------------------------+
| 405         | Operation not allowed.                                 |
+-------------+--------------------------------------------------------+
| 415         | Wrong content type.                                    |
+-------------+--------------------------------------------------------+
| 422         | JSON not valid or not found.                           |
+-------------+--------------------------------------------------------+
| 500         | Internal error.                                        |
+-------------+--------------------------------------------------------+
| 501         | Method not implemented.                                |
+-------------+--------------------------------------------------------+
| 503         | Service maintenance.                                   |
+-------------+--------------------------------------------------------+
| 506         | Wrong response from the database.                      |
+-------------+--------------------------------------------------------+

.. _intro_schema:

Schema
------

API access is exclusively over HTTPS and accessed via the
``api.kernelci.org`` URL.

Data is sent and received **only** in JSON format.

For more info about the resources schema, refer to their :ref:`schema declaration <schema>`.

.. _intro_schema_results:

Results
*******

Query results will always include the ``code`` field reporting the
:ref:`HTTP status code <http_status_code>`. Actual query results
will be included in the ``result`` field and it will always be a list: ::

    {"code": 200, "result": []}

.. _intro_schema_ids:

IDs
***

ID values in a response object are always wrapped in a JSON object, as follows:

::

    {
        "_id": {
            "$oid": "012345678901234567890123"
        },
        "job_id": {
            "$oid": "012345678901234567890123"
        }
    }

The ID value conforms to the following regular expression: :regexp:`[A-Za-z0-9]{24}`

When accessing resources through their ID, always use the real ID as defined
in the ``$oid`` value:

.. sourcecode:: http

    GET /boot/012345678901234567890123/ HTTP/1.1

.. _intro_schema_time_date:

Time and Date
*************

Timestamps are returned as milliseconds since ``January 1, 1970, 00:00:00
UTC`` and are all UTC.

A timestamp will be encoded as follows: ::

    {"created_on": {"$date": 1406788988347}}

Internally, timestamps are stored in `BSON <http://bsonspec.org/>`_ format.

When using the ``date_range`` parameter in a query:

.. sourcecode:: http

    GET /job?date_range=5 HTTP/1.1

The number indicates how many days of data to consider starting from today's
date at ``23:59 UTC`` to ``00:00 UTC`` of the range date. Internally it will be converted in a timedelta structure using the ``created_on`` field: ::

    {
        "created_on": {
            "$lt": {"$date": 1407542399000},
            "$gte": {"$date": 1407369600000}
        }
    }

When using the ``time_range`` parameter in a query:

.. sourcecode:: http

    GET /trigger/boot?time_range=10 HTTP/1.1

The number indicates the minutes of data to consider starting from todays's date
at UTC time. A value of 10 means to consider the data in the last 10 minutes.
Internally it will be converted in a timedelta structure: ::

    {
        "created_on": {
            "$lt": {"$date": 1436793000000},
            "$gte": {"$date": 1436792400000}
        }
    }

Ranged Searches
***************

With fields of type ``int`` and with date type ones, it is possible to perform ranged
search using the ``gte`` (greater-than-equal) and ``lt`` (less-than) operators.

The syntax to define a ranged search is as follows:

::

    [gte|lt]=field,value

``field`` and ``value`` are separated by a comma (``,``).

The following example will search the ``boot`` resource for boot reports whose
``retries`` value is between ``2`` and ``4``:

.. sourcecode:: http

    GET /boot?gte=retries,2&lt=retries,5 HTTP/1.1

It will be converted as follows: ::

    {
        "retries": {
            "$gte": 2,
            "$lt": 5,
        }
    }

The operators can be repeated multiple times. If repeated more than once for
the same field, the last parsed one will be considerd.

The order in which the arguments are parsed might not be guaranteed.


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

    curl -H 'Authorization: token' https://api.kernelci.org/job


Accepted Encodings
------------------

The server accepts the ``gzip`` coding for the ``Accept-Encoding`` HTTP header.

Responses will be compressed using **gzip**.

.. note::

    It is highly advised to require responses compression from the server, it
    will save considerable amount of transfer time.

Email Reports
-------------

The email reports contain custom headers that can be used by email client.

+----------------------------+-----------------------------+----------------------------+
|                            | Build Report                | Boot Report                |
+============================+=============================+============================+
| ``X-Kernelci-Report-Type`` | Its value will be "build".  | Its value will be "boot".  |
+----------------------------+-----------------------------+----------------------------+
| ``X-Kernelci-Tree``        | The name of the tree/job.                                |
+----------------------------+----------------------------------------------------------+
| ``X-Kernelci-Kernel``      | The name of the kernel.                                  |
+----------------------------+----------------------------------------------------------+
| ``X-Kernelci-Branch``      | The name of the branch.                                  |
+----------------------------+-----------------------------+----------------------------+
| ``X-Kernelci-Lab-Name``    | N/A.                        | The name of the lab.       |
+----------------------------+-----------------------------+----------------------------+

.. _intro_boot_regressions:

Boot Regressions
----------------

Each time a new boot report is uploaded it gets compared, if available, with
the previous one. If a change of state, only from ``PASS`` to ``FAIL``, is
detected, a new regressions will be registered and tracked.

Each tracked regression is simply the registered boot report, contained in a
special data structure. The ``PASS`` state is registered, along with all the
``FAIL`` boot reports.

To uniquely identify each single boot reports and its similar ones, the following
keys are used:

* ``lab_name``
* ``arch``
* ``board``
* ``board_instance``
* ``defconfig_full``
* ``compiler_version_ext``
