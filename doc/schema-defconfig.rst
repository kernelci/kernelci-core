.. _schema_defconfig:

defconfig
---------

A defconfig ``name`` is composed of the job, kernel and defconfig values:
``job``-``kernel``-``defconfig``.

At a lower level the ``defconfig`` is the directory resulting from a kernel build using a defconfig.

.. _schema_defconfig_get:

GET
***

The following schema covers the data that is available with a GET request.

::

    {
        "title": "defconfig",
        "description": "A defconfig as built by the CI loop",
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "The version number of this JSON schema",
                "enum": ["1.0"]
            },
            "name": {
                "type": "string",
                "description": "The name of this object (internally created)"
            },
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
            "dirname": {
                "type": "string",
                "description": "The name of the directory of the defconfig built; it can be different from the actual defconfig name"
            },
            "status": {
                "type": "string",
                "description": "The status of the defconfig",
                "enum": ["FAIL", "PASS", "UNKNOWN"]
            },
            "errors": {
                "type": "integer",
                "description": "Number of errors reported",
                "default": 0
            },
            "warnings": {
                "type": "integer",
                "description": "Number of warnings reported",
                "default": 0
            },
            "arch": {
                "type": "string",
                "description": "The architecture of the defconfig built"
            },
            "build_time": {
                "type": "number",
                "description": "The time taken to build this defconfig"
            },
            "git_url": {
                "type": "string",
                "description": "The URL of the git web interface where the code used to build can be found"
            },
            "git_commit": {
                "type": "string",
                "description": "The git SHA of the commit used for the build"
            },
            "git_branch": {
                "type": "string",
                "description": "The name of the branch"
            },
            "git_describe": {
                "type": "string",
                "description": "The name of the git describe command"
            },
            "build_platform": {
                "type": "array",
                "description": "An array with info about the build platform"
            },
            "modules_dir": {
                "type": "string",
                "description": "Name of the modules directory"
            },
            "modules": {
                "type": "string",
                "description": "Name of the modules file"
            },
            "dtb_dir": {
                "type": "string",
                "description": "Name of the dtb directory"
            },
            "build_log": {
                "type": "string",
                "description": "Name of the build log file in txt format"
            },
            "text_offset": {
                "type": "string"
            },
            "system_map": {
                "type": "string",
                "description": "Name of the system map file"
            },
            "kernel_config": {
                "type": "string",
                "description": "Name of the kernel config file used"
            },
            "kernel_image": {
                "type": "string",
                "description": "Name of the kernel image created"
            },
            "metadata": {
                "type": "object",
                "description": "A free form object that can contain different properties"
            }
        }
    }

.. _schema_defconfig_post:

POST
****

The following schema covers the data that should be available in a build JSON
data file sent to the server.

The ``defconfig`` collection does not support POST requests. This schema is
placed here as a reference document in order to provide correct data to the
server.

::

    {
        "title": "defconfig",
        "description": "A defconfig as built by the CI loop",
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
            "defconfig": {
                "type": "string",
                "description": "The name of the defconfig as reported by the CI loop"
            },
            "build_result": {
                "type": "string",
                "description": "The status of the defconfig",
                "enum": ["FAIL", "PASS", "UNKNOWN"]
            },
            "build_errors": {
                "type": "integer",
                "description": "Number of errors reported",
                "default": 0
            },
            "build_warnings": {
                "type": "integer",
                "description": "Number of warnings reported",
                "default": 0
            },
            "arch": {
                "type": "string",
                "description": "The architecture of the defconfig built"
            },
            "build_time": {
                "type": "number",
                "description": "The time taken to build this defconfig",
                "default": 0
            },
            "git_url": {
                "type": "string",
                "description": "The URL of the git web interface where the code used to build can be found"
            },
            "git_commit": {
                "type": "string",
                "description": "The git SHA of the commit used for the build"
            },
            "git_branch": {
                "type": "string",
                "description": "The name of the branch"
            },
            "git_describe": {
                "type": "string",
                "description": "The name of the git describe command"
            },
            "build_log": {
                "type": "string",
                "description": "Name of the build log file in txt format"
            },
            "build_platform": {
                "type": "array",
                "description": "An array with info about the build platform"
            },
            "dtb_dir": {
                "type": "string",
                "description": "Name of the dtb directory"
            },
            "compiler_version": {
                "type": "string",
                "description": "Description string of the compiler used"
            },
            "kconfig_fragments": {
                "type": "string",
                "description": "The config fragment used"
            },
            "kernel_config": {
                "type": "string",
                "description": "Name of the kernel config file used"
            },
            "kernel_image": {
                "type": "string",
                "description": "Name of the kernel image created"
            },
            "cross_compile": {
                "type": "string",
                "description": "The cross compiler used"
            },
            "modules": {
                "type": "string",
                "description": "Name of the modules file"
            },
            "modules_dir": {
                "type": "string",
                "description": "Name of the modules directory"
            },
            "system_map": {
                "type": "string",
                "description": "Name of the system map file"
            },
            "text_offset": {
                "type": "string"
            }
        },
        "required": ["version", "job", "kernel", "defconfig"]
    }


More Info
*********

* :ref:`Defconfig collection <collection_defconfig>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
