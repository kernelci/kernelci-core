.. _schema_attachment:

attachment
----------

An `attachment` object is identified by two elements:

1. Its server URI.
2. Its path on the server URI.

The server URI is defined as the scheme and the authority in `URI notation <http://tools.ietf.org/html/rfc3986#section-3>`_; the attachment
path concides with the path in `URI notation <http://tools.ietf.org/html/rfc3986#section-3>`_:

::

    foo://example.net/I/am/a/file.txt
    \_/   \_________/\______________/
     |         |             |
   scheme  authority        path

Attachments can be uploaded using the :ref:`upload API <collection_upload>`.


.. literalinclude:: schema/1.0/attachment.json
    :language: json

Notes
*****

* ``server_uri``: If this field is not specified, it will default to ``storage.kernelci.org``.

More Info
*********

* :ref:`Upload API <collection_upload>`
* :ref:`API results <intro_schema_results>`
* `Uniform Resource Identifier (URI) <http://tools.ietf.org/html/rfc3986>`_
