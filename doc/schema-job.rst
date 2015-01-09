.. _schema_job:

job
---

A job ``name`` is composed of an actual job name and a kernel name: ``job``-``kernel``.

At a lower level, a job is the top level directory of the results from a CI
build.

.. _schema_job_get:

GET
***

::

    {
        "title": "job",
        "description": "A job as provided by the CI loop",
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "The version number of this JSON schema",
                "enum": ["1.0"]
            },
            "_id": {
                "type": "string",
                "description": "The ID associated with this object"
            },
            "name": {
                "type": "string",
                "description": "The name of the object"
            },
            "created_on": {
                "type": "object",
                "description": "Creation date of the object",
                "properties": {
                    "$date": {
                        "type": "number",
                        "description": "Milliseconds from epoch time"
                    }
                }
            },
            "private": {
                "type": "boolean",
                "description": "If the job is private or not",
                "default": false
            },
            "kernel": {
                "type": "string",
                "description": "The name of the kernel"
            },
            "job": {
                "type": "string",
                "description": "The name of the job"
            },
            "status": {
                "type": "string",
                "description": "The status of the job",
                "enum": ["BUILD", "FAIL", "PASS", "UNKNOWN"]
            },
            "git_branch": {
                "type": "string",
                "description": "The name of the branch"
            },
            "git_commit": {
                "type": "string",
                "description": "The git SHA of the commit used for the build"
            },
            "git_describe": {
                "type": "string",
                "description": "The name of the git describe command"
            },
            "git_url": {
                "type": "string",
                "description": "The URL of the git web interface where the code used to build can be found"
            }
        }
    }

.. _schema_job_post:

POST
****

The following schema covers the data that should be available in the job JSON
data sent to the server.

::

    {
        "title": "job",
        "description": "A job data to trigger build import",
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "The version number of this JSON schema",
                "enum": ["1.0"]
            },
            "job": {
                "type": "string",
                "description": "The job associated with this object"
            },
            "kernel": {
                "type": "string",
                "description": "The kernel associated with this object"
            },
            "boot_report": {
                "type": "boolean",
                "description": "If the boot report should be created and sent",
                "default": 0
            },
            "build_report": {
                "type": "boolean",
                "description": "If the build report should be created and sent",
                "default": 0
            },
            "boot_send_to": {
                "type": ["array", "string"],
                "description": "A single email address or a list of addresses where to send the boot report"
            },
            "build_send_to": {
                "type": ["array", "string"],
                "description": "A single email address or a list of addresses where to send the build report"
            },
            "send_to": {
                "type": ["array", "string"],
                "description": "A single email address or a list of addresses where to send the reports"
            }
        },
        "required": ["job", "kernel"]
    }

Notes
+++++

* By default boot and build reports will not be created nor sent. It is necessary to explicitly set both via ``boot_report`` and ``build_report``.

* ``boot_send_to`` and ``build_send_to`` will each be combined with ``send_to`` to create a list of email addresses (``boot_send_to`` + ``send_to``; ...).


More Info
*********

* :ref:`Job collection <collection_job>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
