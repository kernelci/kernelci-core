.. _schema_job:

job
---

A job ``name`` is composed of an actual job name and a kernel name: ``job``-``kernel``.

At a lower level, a job is the combination of a tree (or Linux repository) and
the name of the kernel that are being built. The tree name is an arbitrary name
associated with the repository; the kernel value usually is the output of the
**git-describe** command:

* ``git://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git`` is the tree called ``mainline``.
* The ``kernel``, for example, could be **v4.0-rc3-194-g5fb0f7fa7f6e**.

In the JSON schema, the above example would become: **mainline-v4.0-rc3-194-g5fb0f7fa7f6e**

.. _schema_job_get:

GET
***

.. note::
    Some of the values describe here are not declared in the POST schema.
    They are taken from the :ref:`defconfig schema <schema_defconfig>` at
    import time and reported here for easier search.

.. literalinclude:: schema/1.0/job_get.json
    :language: json

.. _schema_job_post:

POST
****

The following schema covers the data that should be available in the JSON
data sent to the server.

.. literalinclude:: schema/1.0/job_post.json
    :language: json


More Info
*********

* :ref:`Job resource <collection_job>`
* :ref:`API results <intro_schema_results>`
* :ref:`Defconfig schema <schema_defconfig>`
* :ref:`Schema time and date <intro_schema_time_date>`
