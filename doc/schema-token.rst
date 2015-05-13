.. _schema_token:

token
-----

A token object as stored in the database.

.. _schema_token_get:

GET
***

.. literalinclude:: schema/1.0/get_token.json
    :language: json

.. _schema_token_post:

POST
****

.. literalinclude:: schema/1.0/post_token.json
    :language: json

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
| 7        | If the token is a boot lab token.   |
+----------+-------------------------------------+
| 8        | If the token can upload files.      |
+----------+-------------------------------------+
| 9        | If the token is a test lab token.   |
+----------+-------------------------------------+
| 10 - 15  | Not used.                           |
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

Boot Lab
++++++++

A boot lab token is a token that is being used inside a lab for boot testing.
This property is used only internally to describe the token.

Test Lab
++++++++

A test lab token is a token that is being used to run general tests.
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

