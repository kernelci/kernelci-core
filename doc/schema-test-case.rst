.. _schema_test_case:

test_case
---------

A test case is the single unit of test that gets executed. Each test must have its
own ``name`` defined.

A test case can be associated with only one :ref:`test suite <schema_test_suite>` and one :ref:`test set <schema_test_set>`.

A test case can also register multiple :ref:`measurements <schema_measurement>`.

.. _schema_test_case_get:

GET
***

.. literalinclude:: schema/1.0/test_case_get.json
    :language: json

.. _schema_test_case_post:

POST
****

.. literalinclude:: schema/1.0/test_case_post.json
    :language: json

Notes
+++++

* ``attachments``: Each :ref:`attachment <schema_attachment>` referenced here, must be available at its specified URI or uploaded using the :ref:`upload API <collection_upload>`.

More Info
*********

* :ref:`Test suite schema <schema_test_suite>`
* :ref:`Test set schema <schema_test_set>`
* :ref:`Attachment schema <schema_attachment>`
* :ref:`Measurement schema <schema_measurement>`
* :ref:`File upload API <collection_upload>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
