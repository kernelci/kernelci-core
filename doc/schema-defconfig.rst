.. _schema_defconfig:

defconfig
---------

A defconfig ``name`` is composed of the job, kernel and defconfig values:
``job``-``kernel``-``defconfig_full``.

A defconfig is the result of a build from the continuous integration system. It
contains all the necessary information about what has been built.

.. _schema_defconfig_get:

GET
***

The following schema covers the data that is available with a GET request.

.. literalinclude:: schema/1.0/get_defconfig.json
    :language: json

.. _schema_defconfig_post:

POST
****

The following schema covers the data that should be available in a build JSON
data file sent to the server.

.. literalinclude:: schema/1.0/post_defconfig.json
    :language: json

Notes
+++++

* ``defconfig_full``: This field should be used to specify the full defconfig name if config fragments have been used. It should not contain the architecture (``arch``) value. If not defined, the ``defconfig`` value will be used. Its value should conform to: ``defconfig[+fragment[+fragment ... ]]``.

* ``file_server_url``, ``file_server_resource``: These fields should be used to provide the base URL and the actual path where boot related files (i.e. boot logs) are stored. ``file_server_url`` defines the base path, like ``http://storage.kernelci.org/``, ``file_server_resource`` defines the path on the server, like ``kernel-ci/next/``. When both resources are available, they should be joined together with the file names to form the actual URL. Implementation and default values are left to the user or the visualization tool using the data.

More Info
*********

* :ref:`Defconfig resource <collection_defconfig>`
* :ref:`Job schema <schema_job>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
