# SPDX-License-Identifier: LGPL-2.1-or-later
#
# Copyright (C) 2022, 2023 Collabora Limited
# Author: Guillaume Tucker <guillaume.tucker@collabora.com>

# Needed to use open() in dictionary comprehension
# pylint: disable=consider-using-with

"""KernelCI storage implementation for kernelci-backend"""

import time
from urllib.parse import urljoin
import requests
from . import Storage


class StorageBackend(Storage):
    """Storage implementation for kernelci-backend

    This class implements the Storage interface for the kernelci-backend API.
    It requires an API token as credentials.
    """

    def _close_files(self, files):
        """Helper to close all file handles in the files dictionary."""
        for file_tuple in files.values():
            if hasattr(file_tuple[1], 'close'):
                file_tuple[1].close()

    def _upload(self, file_paths, dest_path):
        headers = {
            'Authorization': self.credentials,
        }
        data = {
            'path': dest_path,
        }

        max_retries = 5
        retry_delay = 10  # seconds
        last_exception = None

        for attempt in range(max_retries):
            try:
                # Re-open files for each attempt since they get consumed
                files = {
                    f'file{i}': (file_dst, open(file_src, 'rb'))
                    for i, (file_src, file_dst) in enumerate(file_paths)
                }

                url = urljoin(self.config.api_url, 'upload')
                resp = requests.post(
                    url, headers=headers, data=data, files=files, timeout=300
                )
                resp.raise_for_status()

                # Success - close files and return
                self._close_files(files)
                return

            except (requests.exceptions.ReadTimeout,
                    requests.exceptions.ConnectionError,
                    requests.exceptions.Timeout) as exc:
                # Close any open files before retry
                if 'files' in locals():
                    self._close_files(files)

                last_exception = exc
                if attempt < max_retries - 1:
                    print(f"Upload attempt {attempt + 1} failed with {type(exc).__name__}: {exc}")
                    print(f"Retrying in {retry_delay} seconds... "
                          f"({max_retries - attempt - 1} retries remaining)")
                    time.sleep(retry_delay)
                else:
                    print(f"Upload failed after {max_retries} attempts")

            except Exception:
                # Close files on any other exception and re-raise
                if 'files' in locals():
                    self._close_files(files)
                raise

        # If we exhausted all retries, raise the last exception
        if last_exception:
            raise last_exception


def get_storage(config, credentials):
    """Get a StorageBackend object"""
    return StorageBackend(config, credentials)
