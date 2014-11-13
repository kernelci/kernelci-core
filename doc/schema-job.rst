.. _schema_job:

job
---

A job ``name`` composed of an actual job name and a kernel name: ``job``-``kernel``.

At a lower level, a job is the top level directory of the results from a CI
build.

::

    {
        "title": "job",
        "description": "A job as provided by the CI loop",
        "type": "object",
        "properties": {
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
            }
        }
    }

More Info
*********

* :ref:`Job collection <collection_job>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
