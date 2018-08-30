.. _schema_test_case:

test_case
---------

A test case is the single unit of test that gets executed. Each test must have
its own ``name`` defined and must be associated with a
:ref:`test suite <schema_test_suite>`.

A test case can be associated with only one
:ref:`test suite <schema_test_suite>`. A test case can also register
multiple :ref:`measurements <schema_measurement>`.

A test case ``name`` must start and end with an alphanumeric character, and it
must match the following regular expression: ``[a-zA-Z0-9.-_+]+``

.. _schema_test_case_get:

GET
***

.. literalinclude:: schema/1.0/get_test_case.json
    :language: json

.. _schema_test_case_post:

POST
****

.. literalinclude:: schema/1.0/post_test_case.json
    :language: json

Notes
+++++

* ``attachments``: Each :ref:`attachment <schema_attachment>` referenced here, must be available at its specified URI or uploaded using the :ref:`upload API <collection_upload>`.

More Info
*********

* :ref:`Test suite schema <schema_test_suite>`
* :ref:`Attachment schema <schema_attachment>`
* :ref:`Measurement schema <schema_measurement>`
* :ref:`File upload API <collection_upload>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
