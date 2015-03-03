.. _schema_test_suite:

test_suite
----------

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
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
