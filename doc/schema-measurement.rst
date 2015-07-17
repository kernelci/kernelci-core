.. _schema_measurement:

measurement
-----------

A measurement object is used to store a measure registered by a test.

.. literalinclude:: schema/1.0/measurement.json
    :language: json

Notes
+++++

For the ``measure`` field, the following conversions are applied based on the specified ``unit``:

* ``number``: Will be treated as a floating point number.
* ``integer``: Will be treated as an integer number; if a floating point number was provided, details/precision of the value will be lost.
* ``time``: Will be treated as an integer describing the total number of seconds.
* ``epoch``: Will be treated as an integer describing the milliseconds from epoch time (1970-01-01).
* ``watt``, ``volt``: Will be treated as floating point numbers.
* ``string``: Will be treated as a normal string.

More Info
*********

* :ref:`Test case schema <schema_test_case>`
* :ref:`API results <intro_schema_results>`
