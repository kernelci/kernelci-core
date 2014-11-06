.. _schema_boot:

boot
----

.. _schema_boot_get:

GET
***

A boot ID is composed from the name of the board, the job, kernel and
defconfig: ``board``-``job``-``kernel``-``defconfig``.

The value of ``defconfig``, in this case, is the directory name containing the
defconfig.

::

    {
        "title": "boot",
        "description": "A boot report object",
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
                        "description": "Milliseconds from epoch time",
                        "format": "utc-millisec"
                    }
                }
            },
            "board": {
                "type": "string",
                "description": "The name of the board"
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
            "time": {
                "type": "object",
                "description": "Time take to boot the board as milliseconds from epoch",
                "properties": {
                    "$date": {
                        "type": "number",
                        "description": "Milliseconds from epoch time"
                    }
                }
            },
            "status": {
                "type": "string",
                "description": "The status of the boot report",
                "enum": ["FAIL", "OFFLINE", "PASS"]
            },
            "warnings": {
                "type": "number",
                "description": "Numbere of warnings in the boot phase"
            },
            "boot_log": {
                "type": "string",
                "description": "Name of the boot log text file"
            },
            "boot_log_html": {
                "type": "string",
                "description": "Name of the boot log HTML file"
            },
            "initrd_addr": {
                "type": "string",
                "description": "Initrd address used"
            },
            "load_addr": {
                "type": "string",
                "description": "Load address used"
            },
            "kernel_image": {
                "type": "string",
                "description": "The kernel image used to boot"
            },
            "dtb_addr": {
                "type": "string",
                "description": "The DTB address used"
            },
            "dtb": {
                "type": "string",
                "description": "The DTB file or directory used"
            },
            "endianness": {
                "type": "string",
                "description": "Endianness of the board"
            },
            "fastboot": {
                "type": "boolean",
                "description": "If it was a fastboot"
            },
            "metadata": {
                "type": "object",
                "description": "A free form object that can contain different properties"
            }
        }
    }

.. _schema_boot_post:

POST
****

The following schema defines the valid fields that a boot report document should
have when sent to the server.

::

    {
        "title": "boot",
        "description": "A boot POST request object",
        "type": "object",
        "properties": {
            "lab_id": {
                "type": "string",
                "description": "The ID of the lab that is doing the boot tests"
            },
            "job": {
                "type": "string",
                "description": "The job associated with this boot report"
            },
            "kernel": {
                "type": "string",
                "description": "The kernel associated with this boot report"
            },
            "defconfig": {
                "type": "string",
                "description": "The name of the defconfig as reported by the CI loop"
            },
            "board": {
                "type": "string",
                "description": "The name of the board: it must be a valid and recognized name"
            },
            "git_branch": {
                "type": "string",
                "description": "The branch used for boot testing"
            },
            "git_commit": {
                "type": "string",
                "description": "The git SHA of the commit used for boot testing"
            },
            "boot_retries": {
                "type": integer,
                "description": "The number of boot retries that have been performed",
                "default": 0
            },
            "boot_result": {
                "type": "string",
                "description": "The final status of the boot test",
                "enum": ["FAIL", "OFFLINE", "PASS"]
            },
            "boot_result_description": {
                "type": "string",
                "description": "The description of the boot result, useful to provide a cause of a failure"
            },
            "boot_log": {
                "type": "string",
                "description": "The name of the boot log file in txt format"
            },
            "boot_log_html": {
                "type": "string",
                "description": "The name of the boot log file in html format"
            },
            "boot_time": {
                "type": "number",
                "description": "The number of seconds it took to boot the board: iternally it will be converted into milliseconds from the epoch time"
            },
            "boot_warnings": {
                "type": "integer",
                "description": "The number of warnings detected during the boot",
                "default": 0
            },
            "dtb": {
                "type": "string",
                "description": "The DTB file or directory used"
            },
            "dtb_addr": {
                "type": "string",
                "description": "The DTB address used"
            },
            "endian": {
                "type": "string",
                "description": "Endianness of the board"
            },
            "fastboot": {
                "type": "boolean",
                "description": "If it was a fastboot"
            },
            "initrd_addr": {
                "type": "string",
                "description": "Initrd address used"
            },
            "kernel_image": {
                "type": "string",
                "description": "The kernel image used to boot"
            },
            "loadaddr": {
                "type": "string",
                "description": "Load address used"
            }
        },
        "required": ["lab_id", "job", "kernel", "defconfig"]
    }


More Info
*********

* :ref:`Boot collection <collection_boot>`
* :ref:`Defconfig schema <schema_defconfig>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
