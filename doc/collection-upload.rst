.. _collection_upload:

upload
------

Upload files to the storage system.

There are two ways to upload files:

1. Through a :http:method:`post` request (:ref:`more info <collection_upload_post>`).

2. Through a :http:method:`put` request (:ref:`more info <collection_upload_put>`).

Using a :http:method:`post` request it is possible to send multiple files at once,
but the request must be encapsulated as ``multipart/form-data``
(:http:header:`Content-Type` header must be ``multipart/form-data``) and it is necessary to specify the **destination directory** where the files should be stored.

Using a :http:method:`put` request, only one file at the time can be uploaded.
The file content must be included in the request body and it is necessary to
specify the **full path** (directory with file name) where the file should be stored.

.. note::

    In order to upload files, the token used must be enabled for such task.

GET
***

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.

.. _collection_upload_post:

POST
****

.. http:post:: /upload

 The destination directory is taken from the data form sent. It first checks
 if a ``path`` parameter is available, otherwise it tries to build the
 destination path with the other form parameters in the following way:
 ``job/git_branch/kernel/arch/[defconfig_full | defconfig ][/lab_name]``

 .. caution::
    Sending multiple times the same files will overwrite the previous ones.

 :formparam path: The destination directory where files should be saved.
 :formparam job: The job name.
 :formparam git_branch: The branch name.
 :formparam kernel: The kernel name.
 :formparam defconfig: The defconfig value.
 :formparam defconfig_full: The defconfig_full value.
 :formparam arch: The architecture type.
 :formparam lab_name: The boot lab name.

 :resjson int code: The status code of the request.
 :resjson array result: An array with the results of each file saved.
 :resjsonarr int status: The status of the file saving operation (can be 200, 201, 500).
 :resjsonarr int bytes: The bytes written to disk.
 :resjsonarr string error: A string with the error reason, in case of errors.
 :resjsonarr string filename: The name of the file as saved.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``multipart/form-data``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: The request has been processed.
 :status 400: Provided request is not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 500: Internal error: cannot write directory, files, ...

 **Example Requests**

 .. sourcecode:: http

    POST /upload/ HTTP/1.1
    Host: api.kernelci.org
    Authorization: token
    Accept: */*
    Content-Type: multipart/form-data; boundary=----------------------------80aa05d1f94c

    ------------------------------80aa05d1f94c
    Content-Disposition: form-data; name="path"

    next/next-20150116/arm-allnoconfig/
    ------------------------------80aa05d1f94c
    Content-Disposition: form-data; name="file01"; filename="zImage"
    Content-Type: application/octet-stream

 .. sourcecode:: http

    POST /upload/ HTTP/1.1
    Host: api.kernelci.org
    Authorization: token
    Accept: */*
    Content-Type: multipart/form-data; boundary=----------------------------80aa05d1f94c

    ------------------------------80aa05d1f94c
    Content-Disposition: form-data; name="job"

    next
    ------------------------------80aa05d1f94c
    Content-Disposition: form-data; name="kernel"

    next-20150116
    ------------------------------80aa05d1f94c
    Content-Disposition: form-data; name="arch"

    arm
    ------------------------------80aa05d1f94c
    Content-Disposition: form-data; name="arch"

    allnoconfig
    ------------------------------80aa05d1f94c
    Content-Disposition: form-data; name="file01"; filename="zImage"
    Content-Type: application/octet-stream

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Fri, 16 Jan 2015 15:12:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result": [
            {
                "status": 200,
                "filename": "zImage",
                "error": null,
                "bytes": 6166840,
            }
        ]
    }

.. _collection_upload_put:

PUT
***

.. http:put:: /upload/(string:path)

 Upload a single file at the specified ``path`` location. ``path`` is the filename
 path where it should be stored. It will be treated like a file path. The file
 content should be sent in the request body.

 :param path: The destination path where the file should be saved.

 :resjson int code: The status code of the request.
 :resjson array result: An array with the results of each file saved.
 :resjsonarr int status: The status of the file saving operation (can be 200, 201, 500).
 :resjsonarr int bytes: The bytes written to disk.
 :resjsonarr string error: A string with the error reason, in case of errors.
 :resjsonarr string filename: The name of the file as saved.

 :reqheader Authorization: The token necessary to authorize the request.
 :reqheader Content-Type: Content type of the transmitted data, must be ``multipart/form-data``.
 :reqheader Accept-Encoding: Accept the ``gzip`` coding.

 :resheader Content-Type: Will be ``application/json; charset=UTF-8``.

 :status 200: The file has been saved and the old one overwritten.
 :status 201: The file has been saved.
 :status 400: Provided request is not valid.
 :status 403: Not authorized to perform the operation.
 :status 415: Wrong content type.
 :status 500: Internal error: cannot write directory, files, ...

 **Example Requests**

 .. sourcecode:: http

    PUT /upload/next/next-20150116/arm-allnoconfig/zImage HTTP/1.1
    Host: api.kernelci.org
    Authorization: token
    Accept: */*
    Content-Length: 6166840
    Content-Type: application/x-www-form-urlencoded

    .7zXZ......F..!.....GX:C..,..].....1.PX.3{...V...!...[.4....3..~
    ...

 **Example Responses**

 .. sourcecode:: http

    HTTP/1.1 200 OK
    Vary: Accept-Encoding
    Date: Fri, 16 Jan 2015 15:12:50 GMT
    Content-Type: application/json; charset=UTF-8

    {
        "code": 200,
        "result": [
            {
                "status": 200,
                "filename": "zImage",
                "error": null,
                "bytes": 6166840,
            }
        ]
    }

DELETE
******

.. caution::
    Not implemented. Will return a :ref:`status code <http_status_code>`
    of ``501``.

More Info
*********

* :ref:`API results <intro_schema_results>`
* :ref:`Schema time and date <intro_schema_time_date>`
