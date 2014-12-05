.. _schema_lab:

lab
---

The ``name`` of the lab mut be a unique value among all the registered labs. Use
a short but descriptive name to identify the lab, since this value will be used
to perform POST request :ref:`on the boot collection <collection_boot_post>`.

As a rule of thumbs for creating a lab ``name``:

* Start the lab name with ``lab-``.

* Use some of the contact information as the next element (the ``name``, or ``affiliation``).
 
* Add a progressive number at the end (``-00``, ``-01``, etc...).

.. _schema_lab_get:

GET
***

::

    {
        "title": "lab",
        "description": "A lab object",
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "The version of this JSON schema: depends on the POST request"
            },
            "name": {
                "type": "string",
                "description": "The name associated with the object"
            },
            "_id": {
                "type": "string",
                "description": "The ID associated with the object as provided by mongodb"
            },
            "created_on": {
                "type": "object",
                "description": "Creation date of the object",
                "properties": {
                    "$date": {
                        "type": "number",
                        "description": "Milliseconds from epoch time",
                        "format": "utc-millisec"
                    }
                }
            },
            "updated_on": {
                "type": "object",
                "description": "Update date of the object",
                "properties": {
                    "$date": {
                        "type": "number",
                        "description": "Milliseconds from epoch time",
                        "format": "utc-millisec"
                    }
                }
            },
            "contact": {
                "type": "object",
                "description": "The contact details of the object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the contact"
                    },
                    "surname": {
                        "type": "string",
                        "description": "The surname of the contact"
                    },
                    "email": {
                        "type": "string",
                        "description": "The email of the contact"
                    },
                    "telephone": {
                        "type": "string",
                        "description": "The landline phone number"   
                    },
                    "mobile": {
                        "type": "string",
                        "description": "The mobile phone number"
                    },
                    "affiliation": {
                        "type": "string",
                        "description": "The name of the company, or association this contact is part of"
                    }
                }
            },
            "address": {
                "type": "object",
                "description": "The address where the lab is located",
                "properties": {
                    "street_1": {
                        "type": "string",
                        "description": "First line for the address"
                    },
                    "street_2": {
                        "type": "string",
                        "description": "Second line for the address"
                    },
                    "city": {
                        "type": "string",
                        "description": "The city name"
                    },
                    "country": {
                        "type": "string",
                        "description": "The country name"
                    },
                    "zipcode": {
                        "type": "string",
                        "description": "The zip code"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Latitude of the lab location"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the lab location"
                    }
                }
            },
            "private": {
                "type": "boolean",
                "description": "If the lab is private or not",
                "default": "false"
            },
            "token": {
                "type": "string",
                "description": "The ID of the token associated with this lab"
            }
        }
    }

.. _schema_lab_post:

POST
****


::

    {
        "title": "lab",
        "description": "A lab object",
        "type": "object",
        "properties": {
            "version": {
                "type": "string",
                "description": "The version number of this JSON schema",
                "enum": ["1.0"]
            },
            "name": {
                "type": "string",
                "description": "The name associated with the object"
            },
            "contact": {
                "type": "object",
                "description": "The contact details of the object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The name of the contact"
                    },
                    "surname": {
                        "type": "string",
                        "description": "The surname of the contact"
                    },
                    "email": {
                        "type": "string",
                        "description": "The email of the contact"
                    },
                    "telephone": {
                        "type": "string",
                        "description": "The landline phone number"   
                    },
                    "mobile": {
                        "type": "string",
                        "description": "The mobile phone number"
                    },
                    "affiliation": {
                        "type": "string",
                        "description": "The name of the company, or association this contact is part of"
                    },
                    "required": ["name", "surname", "email"]
                }
            },
            "address": {
                "type": "object",
                "description": "The address where the lab is located",
                "properties": {
                    "street_1": {
                        "type": "string",
                        "description": "First line for the address"
                    },
                    "street_2": {
                        "type": "string",
                        "description": "Second line for the address"
                    },
                    "city": {
                        "type": "string",
                        "description": "The city name"
                    },
                    "country": {
                        "type": "string",
                        "description": "The country name"
                    },
                    "zipcode": {
                        "type": "string",
                        "description": "The zip code"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Latitude of the lab location"
                    },
                    "longitude": {
                        "type": "number",
                        "description": "Longitude of the lab location"
                    }
                }
            },
            "private": {
                "type": "boolean",
                "description": "If the lab is private or not",
                "default": "false"
            },
            "token": {
                "type": "string",
                "description": "The token to associated with this lab"
            }
        },
        "required": ["version", "name", "contact"]
    }

More Info
*********

* :ref:`Lab collection <collection_lab>`
* :ref:`Defconfig schema <schema_defconfig>`
* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
