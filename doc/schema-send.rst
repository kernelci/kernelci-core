.. _schema_send:

send
----

.. _schema_send_post:

POST
****

The following schema covers the data that should be available in the JSON
data sent to the server.

::

    {
        "title": "send",
        "description": "Data to trigger the email report",
        "type": "object",
        "properties": {
            "job": {
                "type": "string",
                "description": "The job name associated with the object"
            },
            "kernel": {
                "type": "string",
                "description": "The kernel name associated with the object"
            },
            "boot_report": {
                "type": "boolean",
                "description": "Whether the boot report should be created and sent",
                "default": 0
            },
            "build_report": {
                "type": "boolean",
                "description": "Whether the build report should be created and sent",
                "default": 0
            },
            "boot_send_to": {
                "type": ["string", "array"],
                "description": "The emails to sent the boot report to"
            },
            "build_send_to": {
                "type": ["string", "array"],
                "description": "The emails to send the build report to"
            },
            "send_to": {
                "type": ["string", "array"],
                "description": "The emails to send the reports to, will be appended to the more specific email control values"
            }
        },
        "required": ["job", "kernel"]
    }

More Info
*********

* :ref:`Report schema <schema_report>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
