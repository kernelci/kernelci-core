.. _schema_boot:

boot
----

.. _schema_boot_get:

GET
***

A boot ``name`` is composed from the name of the board, job, kernel, defconfig
and architecture values: ``board``-``job``-``kernel``-``defconfig``-``arch``.

Boot report ``name``-s are not unique. To uniquely identify a boot report it is
necessary to use its ``_id`` value.

::

    {
        "title": "boot",
        "description": "A boot report object",
        "type": "object",
        "properties": {
            "name": {
                "type": "string",
                "description": "The name of this boot report (internally created)"
            },
            "_id": {
                "type": "string",
                "description": "The ID associated with the object as provided by mongodb"
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
            "job_id": {
                "type": "object",
                "description": "The ID of the associated job",
                "properties": {
                    "$oid": {
                        "type": "string",
                        "description": "The actual ID value"
                    }
                }
            },
            "kernel": {
                "type": "string",
                "description": "The kernel associated with this object"
            },
            "defconfig": {
                "type": "string",
                "description": "The name of the defconfig as reported by the CI loop"
            },
            "defconfig_full": {
                "type": "string",
                "description": "The full name of the defconfig, can contain also config fragments information",
                "default": "The defconfig value"
            },
            "defconfig_id": {
                "type": "object",
                "description": "The ID of the associated build report",
                "properties": {
                    "$oid": {
                        "type": "string",
                        "description": "The actual ID value"
                    }
                }
            },
            "arch" : {
                "type": "string",
                "description": "The architecture type of this board",
                "enum": ["arm", "arm64", "x86"],
                "default": "arm"
            },
            "git_branch": {
                "type": "string",
                "description": "The branch used for boot testing"
            },
            "git_commit": {
                "type": "string",
                "description": "The git SHA of the commit used for boot testing"
            },
            "git_describe": {
                "type": "string",
                "description": "The name of the git describe command"
            },
            "lab_name": {
                "type": "string",
                "description": "The name of the lab that is doing the boot tests"
            },
            "time": {
                "type": "object",
                "description": "Time taken to boot the board",
                "properties": {
                    "$date": {
                        "type": "number",
                        "description": "Milliseconds from epoch time",
                        "format": "utc-millisec"
                    }
                }
            },
            "status": {
                "type": "string",
                "description": "The status of the boot report",
                "enum": ["FAIL", "OFFLINE", "PASS", "UNTRIED"]
            },
            "warnings": {
                "type": "number",
                "description": "Number of warnings in the boot phase"
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
            "boot_result_description": {
                "type": "string",
                "description": "The description of the boot result, useful to provide a cause of a failure"
            },
            "retries": {
                "type": "integer",
                "description": "The number of boot retries that have been performed",
                "default": 0
            },
            "version": {
                "type": "string",
                "description": "The version of this JSON schema: depends on the POST request"
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
            "version": {
                "type": "string",
                "description": "The version number of this JSON schema",
                "enum": ["1.0"]
            },
            "lab_name": {
                "type": "string",
                "description": "The name of the lab that is doing the boot tests"
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
            "defconfig_full": {
                "type": "string",
                "description": "The full name of the defconfig with config fragments information",
                "default": "The defconfig value"
            },
            "board": {
                "type": "string",
                "description": "The name of the board: it must be a valid and recognized name"
            },
            "arch" : {
                "type": "string",
                "description": "The architecture type of this board",
                "enum": ["arm", "arm64", "x86"],
                "default": "arm"
            },
            "git_branch": {
                "type": "string",
                "description": "The branch used for boot testing"
            },
            "git_commit": {
                "type": "string",
                "description": "The git SHA of the commit used for boot testing"
            },
            "git_describe": {
                "type": "string",
                "description": "The name of the git describe command"
            },
            "boot_retries": {
                "type": "integer",
                "description": "The number of boot retries that have been performed",
                "default": 0
            },
            "boot_result": {
                "type": "string",
                "description": "The final status of the boot test",
                "enum": ["FAIL", "OFFLINE", "PASS", "UNTRIED"]
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
            "dtb_append": {
                "type": "boolean",
                "default": "false"
            },
            "endian": {
                "type": "string",
                "description": "Endianness of the board"
            },
            "fastboot": {
                "type": "boolean",
                "description": "If it was a fastboot",
                "default": "false"
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
            },
            "email": {
                "type": "string",
                "description": "Optional email address to be notified if the boot report import fails"
            }
        },
        "required": ["version", "lab_name", "job", "kernel", "defconfig", "board", "arch"]
    }

Notes
+++++

* ``defconfig_full``: This field should be used to specify the entire defconfig used if config fragments have been used and it should not contain the architecture (``arch``) value. Its value should conform to: ``defconfig[+fragment[+fragment ... ]]``

More Info
*********

* :ref:`Boot collection <collection_boot>`
* :ref:`Defconfig schema <schema_defconfig>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
