.. _schema_job:

job
---

At a lower level, a job is the combination of a tree (or repository) and
the name of the "kernel" that are being built.

The tree value is an arbitrary name associated with the repository; the kernel value usually is the output of the **git-describe** command:

* ``git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git`` is the tree called ``mainline``.
* The ``kernel``, for example, could be **v4.0-rc3-194-g5fb0f7fa7f6e**.

.. _schema_job_get:

GET
***

The following schema covers the data that is available with a GET request.

.. note::
    Some of the values describe here are not declared in the POST schema.
    They are taken from the :ref:`defconfig schema <schema_build>` at
    import time and reported here for easier search.

.. literalinclude:: schema/1.1/get_job.json
    :language: json

.. _schema_job_post:

POST
****

The following schema covers the data that should be available in the JSON
data sent to the server.

.. literalinclude:: schema/1.1/post_job.json
    :language: json


More Info
*********

* :ref:`Job resource <collection_job>`
* :ref:`API results <intro_schema_results>`
* :ref:`Defconfig schema <schema_build>`
* :ref:`Schema time and date <intro_schema_time_date>`
