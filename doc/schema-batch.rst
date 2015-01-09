.. _schema_batch:

batch
-----

A batch request object.

::

    {
        "title": "batch",
        "description": "A batch request to perform multiple operations",
        "type": "array",
        "items": {
            "type": "object",
            "properties": {
                "method": {
                    "type": "string",
                    "description": "The method of the request operation as if this operation was performed in a normal HTTP request"
                },
                "operation_id": {
                    "type": "string",
                    "description": "A unique identifier for the operation to perform"
                },
                "collection": {
                    "type": "string",
                    "description": "The resource where to perform the operation"
                },
                "document_id": {
                    "type": "string",
                    "description": "The ID of the document in the collection"
                },
                "query": {
                    "type": "string",
                    "description": "A key=value pairs, separated by the ampersand character, that define the query to perform on the resource"
                }
            }
        }
    }

