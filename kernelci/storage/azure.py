# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

"""KernelCI storage implementation for Azure Files"""

from urllib.parse import urljoin
import os
from azure.storage.fileshare import ShareServiceClient
from . import Storage


class StorageAzureFiles(Storage):
    """Storage implementation for Azure Files

    This class implements the Storage interface for uploading files to Azure
    Files.  It uses a public Shared Access Signature read-only token for the
    download URLs while also relying on a separate token with appropriate
    permissions for uploading files passed as the storage credentials.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._service = None

    def _connect(self):
        if self._service is not None:
            return
        self._service = ShareServiceClient(
            account_url=self.config.base_url,
            credential=self.credentials
        )

    def _get_directory(self, share, path):
        directory = share.get_directory_client(directory_path=path)
        if not directory.exists():
            directory.create_directory()
        return directory

    def _upload(self, file_paths, dest_path):
        share = self._service.get_share_client(share=self.config.share)
        root = self._get_directory(share, dest_path or '.')
        urls = {}
        dirs = []
        # if dst include a path, we need to call ._get_directory
        # to create the directory if it doesn't exist
        # for example if dst is 'dtb/qcom/apq8016-sbc.dtb'
        # get list of all directories to create, then create them
        for src, dst in file_paths:
            if os.path.dirname(dst) and os.path.dirname(dst) not in dirs:
                dirs.append(os.path.dirname(dst))
        for dname in dirs:
            dstdir = os.path.join(dest_path, dname)
            self._get_directory(share, dstdir)
        for src, dst in file_paths:
            file_client = root.get_file_client(file_name=dst)
            with open(src, 'rb') as src_file:
                file_client.upload_file(src_file)
            urls[dst] = urljoin(
                self.config.base_url,
                '/'.join([self.config.share, dest_path, dst]),
            ) + self.config.sas_public_token
        return urls


def get_storage(config, credentials):
    """Get a StorageAzureFiles object"""
    return StorageAzureFiles(config, credentials)
