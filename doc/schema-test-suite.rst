.. _schema_test_suite:

test_suite
----------

A test suite is the collection of :ref:`test cases <schema_test_case>`.

A test suite must define its own ``name`` and must be associated with a :ref:`lab <schema_lab>` and with a :ref:`build <schema_build>`. The association with the ``build`` object is performed through the ``build_id`` value, the lab association via the lab ``name`` value.

A test suite ``name`` must start and end with an alphanumeric character, and it
must match the following regular expression: ``[a-zA-Z0-9.-_+]+``

.. _schema_test_suite_get:

GET
***

.. literalinclude:: schema/1.0/get_test_suite.json
    :language: json

Notes
+++++

* ``test_case``: By default, the API will provide the IDs of the ``test_case`` objects. To expand the selection in order to include the actual objects, please refer to the ``test`` resource query arguments.

.. _schema_test_suite_post:

POST
****

.. literalinclude:: schema/1.0/get_test_suite.json
    :language: json

Notes
+++++

* ``test_case``: If not specified, the test case executed must be registered using the appropriate API call.

More Info
*********

* :ref:`Test case schema <schema_test_case>`
* :ref:`Defconfig schema <schema_build>`
* :ref:`Lab schema <schema_lab>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
