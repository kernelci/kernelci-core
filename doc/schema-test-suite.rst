.. _schema_test_suite:

test_suite
----------

A test suite is the collection of :ref:`test sets <schema_test_set>` and :ref:`test cases <schema_test_case>`.

A test suite must define its own ``name`` and must be associated with a :ref:`lab <schema_lab>` and with a :ref:`built defconfig <schema_defconfig>`. The association with the ``defconfig`` object is performed through the ``defconfig_id`` value, the lab association via the lab ``name`` value.

.. _schema_test_suite_get:

GET
***

.. literalinclude:: schema/1.0/test_suite_get.json
    :language: json

Notes
+++++

* ``test_set``, ``test_case``: By default, the API will provide the IDs of the ``test_set`` and ``test_case`` objects. To expand the selection in order to include the actual objects, please refer to the ``test`` resource query arguments.

.. _schema_test_suite_post:

POST
****

.. literalinclude:: schema/1.0/test_suite_post.json
    :language: json

Notes
+++++

* ``test_set``: If not specified, the test set executed must be registered using the appropiate API call.

* ``test_case``: If not specified, the test case executed must be registered using the appropriate API call.

More Info
*********

* :ref:`Test set schema <schema_test_set>`
* :ref:`Test case schema <schema_test_case>`
* :ref:`Defconfig schema <schema_defconfig>`
* :ref:`Lab schema <schema_lab>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
