.. _schema_test_set:

test_set
--------

A test set is a collection of :ref:`test cases <schema_test_case>`. Each test set
must define its own ``name`` and must be associated with a :ref:`test suite <schema_test_suite>`.

.. _schema_test_set_get:

GET
***

.. literalinclude:: schema/1.0/get_test_set.json
    :language: json

Notes
+++++

* ``test_case``: By default, the API will provide the IDs of the ``test_case`` objects. To expand the selection in order to include the actual objects, please refer to the ``test`` resource query arguments.

.. _schema_test_set_post:

POST
****

.. literalinclude:: schema/1.0/post_test_set.json
    :language: json

Notes
+++++

* ``test_case``: If not specified, the test case executed must be registered using the appropriate API call.
* ``test_job_path``: The path of the test job executor URI *should* contain the job ID. The ``test_job_id`` field is used for searching.

More Info
*********

* :ref:`Test suite schema <schema_test_suite>`
* :ref:`Test case schema <schema_test_case>`
* :ref:`Test defect schema <schema_test_defect>`
* `URI syntax components <http://tools.ietf.org/html/rfc3986#section-3>`_
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
