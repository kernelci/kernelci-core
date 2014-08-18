.. _schema_boot:

boot
----

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
                        "description": "Milliseconds from epoch time"
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
                "items": {
                    "FAIL",
                    "PASS",
                    "OFFLINE"
                }
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

More Info
*********

* :ref:`Defconfig schema <schema_defconfig>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
