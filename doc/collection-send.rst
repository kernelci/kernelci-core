.. _collection_send:

send
----

Trigger email reports for boot and build tests.

More info about the send schema can be found :ref:`here <schema_send>`.

GET
***

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.

.. note::

    For information about the triggered email reports, see :ref:`the report resource <collection_report>`

POST
****

.. http:post:: /send

 Schedule boot and/or build email report.

 For more info on all the required JSON request fields, see the :ref:`schema for POST requests <schema_send_post>`.

 :reqjson string job: The name of the job.
 :reqjson string kernel: The name of the kernel.
 :reqjson boolean boot_report: If the boot report should be created and sent. Default to 0 (false).
 :reqjson boolean build_report: If the build report should be created and sent. Default to 0 (false).
 :reqjson send_to: A string or an array of strings of email addresses where to send the reports.
 :reqjson boot_send_to: A string or an array of strings of email addresses where to send only the boot report.
 :reqjson build_send_to: A string or an array of strings of email addresses where to send only the build report.
 :reqjson int delay: Number of seconds after which the email report will be sent. Default to 60*60 seconds.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``application/json``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 202: The request has been accepted and will be processed.
 :status 400: JSON data not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 422: No real JSON data provided.

 **Example Requests**

 .. sourcecode:: http 

    POST /send HTTP/1.1
    Host: api.kernelci.org
    Content-Type: application/json
    Accept: */*
    Authorization: token

    {
        "job": "next",
        "kernel": "next-20140801",
        "boot_report": 1,
        "send_to": ["email@example.net"],
        "delay": 14400
    }

DELETE
******

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.

More Info
*********

* :ref:`Send schema <schema_send>`
* :ref:`Send report <schema_report>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
