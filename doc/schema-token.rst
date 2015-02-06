.. _schema_token:

token
-----

A token object as stored in the database.

.. _schema_token_get:

GET
***

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

.. _schema_token_post:

POST
****

::

    {
        "title": "token",
        "description": "The JSON schema to create/update tokens",
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "The version number of this JSON schema",
                "enum": ["1.0"]
            },
            "email": {
                "type": "string",
                "description": "The email address asscoaited with the token"
            },
            "username": {
                "type": "string",
                "description": "The user name associated with the token"
            },
            "expired": {
                "type": "boolean",
                "description": "If the token has expired"
            },
            "expires_on": {
                "type": "string",
                "description": "The date when the token is supposed to expire in the format YYYY-MM-DD"
            },
            "get": {
                "type": "boolean",
                "description": "If the token can perform GET operations"
            },
            "post": {
                "type": "boolean",
                "description": "If the token can perform POST/PUT operations"
            },
            "delete": {
                "type": "boolean",
                "description": "If the token can perfrom DELETE operations"
            },
            "upload": {
                "type": "boolean",
                "description": "If the token can be used to upload files"
            },
            "admin": {
                "type": "boolean",
                "description": "If the token is an admin token"
            },
            "superuser": {
                "type": "boolean",
                "description": "If the token is a super user one"
            },
            "lab": {
                "type": "boolean",
                "description": "If the token is used by a lab (i.e. a boot lab)"
            },
            "ip_restricted": {
                "type": "boolean",
                "description": "If the token is IP restricted"
            },
            "ip_address": {
                "type": "array",
                "description": "Array of IP addresses the token is restricted to"
            }
        },
        "required": ["email"]
    }

.. note::

    In case of a POST request to **update an existing token** the required field is not mandatory.

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
| 3        | If the token can perform POST/PUT.  |
+----------+-------------------------------------+
| 4        | If the token can perform DELETE.    |
+----------+-------------------------------------+
| 5        | If the token is IP restricted.      |
+----------+-------------------------------------+
| 6        | If the token can create new tokens. |
+----------+-------------------------------------+
| 7        | If the token is a lab token.        |
+----------+-------------------------------------+
| 8        | If the token can upload files.      |
+----------+-------------------------------------+
| 9 - 15   | Not used.                           |
+----------+-------------------------------------+

Other Token Info
****************

Administrator & Superuser Tokens
================================

An administrator token can perform all operations: GET, DELETE, POST/PUT and can upload files.
It can also create new tokens and update existing ones.

A superuser token can perform all operations: GET, DELETE, POST/PUT and can upload files.
It cannot create new tokens nor update existing ones.

Lab Token
=========

A lab token is a token that is being used inside a lab, usually for boot testing.
This property is used only internally to describe the token.

IP Restricted Token
===================

A token can be restricted to be used only from one or more IP addresses.
IP addresses can be specified as a single IP address (i.e. 192.168.1.0) or as
a network of IP addresses (i.e. 192.0.3.112/22).

Both IPv4 and IPv6 are supported.

More Info
*********

* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`

