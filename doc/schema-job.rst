.. _schema_job:

job
---

A job is composed of an actual job name and a kernel name. The ID is formed
by concatenating these two values: ``job``-``kernel``.

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
                "description": "If the job is private or not, default false"
            },
            "kernel": {
                "type": "string",
                "description": "The name of the kernel"
            },
            "updated": {
                "type": "object",
                "description": "Date the job was updated",
                "properties": {
                    "$date": {
                        "type": "number",
                        "description": "Milliseconds from epoch time"
                    }
                }
            },
            "job": {
                "type": "string",
                "description": "The name of the job"
            },
            "status": {
                "type": "string",
                "description": "The status of the job",
                "items": {
                    "BUILD",
                    "FAIL",
                    "PASS",
                    "UNKNOWN"
                }
            },
            "metadata": {
                "type": "object",
                "description": "A free form object that can contain different properties",
                "properties": {
                    "git_branch": {
                        "type": "string",
                        "description": "The kernel branch name"
                    },
                    "git_commit": {
                        "type": "string",
                        "description": "The commit SHA"
                    },
                    "git_url": {
                        "type": "string",
                        "description": "URL of the git repository"
                    },
                    "git_describe": {
                        "type": "string",
                        "description": "Name of the repository"
                    }
                }
            }
        }
    }

More Info
*********

* :ref:`Job collection <collection_job>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
