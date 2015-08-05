.. _schema_lab:

lab
---

The ``name`` of the lab must be a unique value among all the registered labs.
Use a short but descriptive name to identify the lab, since this value will be
used to perform POST request :ref:`on the boot resource <collection_boot_post>`.

As a rule of thumbs for creating a lab ``name``:

* Start the lab name with ``lab-``.

* Use some of the contact information as the next element (the ``name``, or ``affiliation``).
 
* Add a progressive number at the end (``-00``, ``-01``, etc...).

.. _schema_lab_get:

GET
***

.. literalinclude:: schema/1.0/get_lab.json
    :language: json

.. _schema_lab_post:

POST
****

.. literalinclude:: schema/1.0/post_lab.json
    :language: json

Notes:

* The mandatory fields for ``POST`` requests are not required for ``PUT`` requests.

More Info
*********

* :ref:`Lab resource <collection_lab>`
* :ref:`Defconfig schema <schema_build>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
