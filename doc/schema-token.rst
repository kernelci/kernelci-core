.. _schema_token:

token
-----

A token object as stored in the database.

::

    {
        "title": "token",
        "description": "A token used to interact with the API",
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "The version number of this JSON schema",
                "enum": ["1.0"]
            },
            "_id": {
                "type": "string",
                "description": "The ID associated with this object"
            },
            "name": {
                "type": "string",
                "description": "The name associated with this token"
            },
            "created_on": {
                "type": "object",
                "description": "Creation date of the object",
                "properties": {
                    "$date": {
                        "type": "number",
                        "description": "Milliseconds from epoch time"
                    }
                }
            },
            "token": {
                "type": "string",
                "description": "The token that will be used to interact with the API"
            },
            "expires_on": {
                "type": "object",
                "description": "The date when the token is supposed to expire",
                "properties": {
                    "$date": {
                        "type": "number",
                        "description": "Milliseconds from epoch time"
                    }
                }
            },
            "expired": {
                "type": "boolean",
                "description": "If the token has expired"
            },
            "username": {
                "type": "string",
                "description": "The user name associated with the token"
            },
            "email": {
                "type": "string",
                "description": "The email address asscoaited with the token"
            },
            "ip_address": {
                "type": "array",
                "description": "List of IP addresses the token is restricted to"
            },
            "properties": {
                "type": "array",
                "description": "An array of length 16 of integer values; each value defines a properties of the token"
            }
        }
    }

Token Properties
****************

The following table describes the ``properties`` array of a token:

+----------+-------------------------------------+
| Position | Description                         |
+==========+=====================================+
| 0        | If the token is an admin token.     |
+----------+-------------------------------------+
| 1        | If the token is a super-user token. |
+----------+-------------------------------------+
| 2        | If the token can perform GET.       |
+----------+-------------------------------------+
| 3        | If the token can perform POST.      | 
+----------+-------------------------------------+
| 4        | If the token can perform DELETE.    |
+----------+-------------------------------------+
| 5        | If the token is IP restricted.      |
+----------+-------------------------------------+
| 6        | If the token can create new tokens. |
+----------+-------------------------------------+
| 7 - 15   | Not used.                           |
+----------+-------------------------------------+

More Info
*********

* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`

