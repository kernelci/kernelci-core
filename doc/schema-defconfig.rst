.. _schema_defconfig:

defconfig
---------

A defconfig ID is composed of a job ID and the defconfig name as follows:
``job``-``kernel``-``name``.

At a lower level a defconfig is the directory resulting from a kernel build
using a defconfig.

::

    {
        "title": "defconfig",
        "description": "A defconfig as built by the CI loop",
        "type": "object",
        "properties": {
            "_id": {
                "type": "string",
                "description": "The ID associated with the object"
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
            "job": {
                "type": "string",
                "description": "The job associated with this object"
            },
            "kernel": {
                "type": "string",
                "description": "The kernel associated with this object"
            },
            "defconfig": {
                "type": "string",
                "description": "The name of the defconfig as reported by the CI loop"
            },
            "dirname": {
                "type": "string",
                "description": "The name of the directory of the defconfig built; it can be different from the actual defconfig name"
            },
            "status": {
                "type": "string",
                "description": "The status of the defconfig",
                "items": {
                    "FAIL",
                    "PASS",
                    "UNKNOWN"
                }
            },
            "errors": {
                "type": "number",
                "description": "Number of errors reported"
            },
            "warnings": {
                "type": "number",
                "description": "Number of warnings reported"
            },
            "arch": {
                "type": "string",
                "description": "The architecture of the defconfig built"
            },
            "metadata": {
                "type": "object",
                "description": "A free form object that can contain different properties"
            }
        }
    }

More Info
*********

* :ref:`Defconfig collection <collection_defconfig>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
