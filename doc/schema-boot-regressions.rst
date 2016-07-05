.. _schema_boot_regressions:

boot_regressions
----------------

.. _schema_boot_regressions_get:

GET
***

The following schema covers the data that is available with a GET request.

.. literalinclude:: schema/1.0/get_boot_regressions.json
    :language: json

Notes
+++++

The ``regressions`` data structure is a series of nested objects whose keys are,
in order, the values of the following boot report keys:

* ``lab_name``
* ``arch``
* ``board``
* ``board_instance``
* ``defconfig_full``
* ``compiler_version_ext``

If one of those keys does not have a valid value, the string ``none`` is used.
Each of those value is also checked and sanitized so taht it doesn't contain
empty spaces or the character ``.``.

The actual regressions are stored in an array as the value of the
``compiler_version_ext`` key. Each regression is a valid :ref:`boot report <schema_boot>`.

The boot reports contained in the regressions array are inserted as a time-series
data, but not guarantees are mare on their sort order once extracted.

Example
=======

::

    {
        "lab-0001": {
            "arm": {
                "beaglebone": {
                    "none": {
                        "allmodconfig": {
                            "gcc5:3:1": [
                                ...
                            ]
                        }
                    }
                }
            }
        }
    }


More Info
*********

* :ref:`Boot resource <collection_boot>`
* :ref:`Defconfig schema <schema_build>`
* :ref:`API results <intro_schema_results>`
* :ref:`Boot regressions <intro_boot_regressions>`
