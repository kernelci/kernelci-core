.. _schema_boot:

boot
----

.. _schema_boot_get:

GET
***

The following schema covers the data that is available with a GET request.

.. literalinclude:: schema/1.1/get_boot.json
    :language: json

.. _schema_boot_post:

POST
****

The following schema defines the valid fields that a boot report document should
have when sent to the server.

.. literalinclude:: schema/1.1/post_boot.json
    :language: json

Notes
+++++

* ``defconfig_full``: This field should be used to specify the full defconfig name if config fragments have been used. It should not contain the architecture (``arch``) value. If not defined, the ``defconfig`` value will be used. Its value should conform to: ``defconfig[+fragment[+fragment ... ]]``.

* ``file_server_url``, ``file_server_resource``: These field should be used to provide the base URL and the actual path where boot related files (i.e. boot logs) are stored. ``file_server_url`` defines the base path, like ``http://storage.kernelci.org/``, ``file_server_resource`` defines the path on the server, like ``kernel-ci/next/``. When both resources are available, they should be joined together with the file names to form the actual URL. Implementation and default values are left to the user or the visualization tool using the data.

* ``boot_job_path``: The path of the boot test job executor URI *should* contain the job ID. The ``boot_job_id`` field is used for searching and visualization.

More Info
*********

* :ref:`Boot resource <collection_boot>`
* :ref:`Defconfig schema <schema_build>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
