#!/usr/bin/env python3
#
# Copyright (C) 2023 Collabora Limited
# Author: Alexandra Pereira <alexandra.pereira@collabora.com>
#
# This script is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation; either version 2.1 of the License, or (at your option)
# any later version.
#
# This library is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License
# along with this library; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA

import argparse
import re
import requests
import subprocess
import sys
from urllib.parse import urljoin

TAST_PATH = './tast'


def fetch_dut():
    output = subprocess.check_output("lava-target-ip", shell=True).strip()
    return output


def get_tast_tests(output_filename):
    try:
        remote_ip = fetch_dut()
        cmd = [
            TAST_PATH,
            'list',
            '-json',
            '-build=false',
            remote_ip
        ]
        with open(output_filename, 'w') as test_output_file:
            subprocess.run(cmd, check=True, stdout=test_output_file)
        return True
    except OSError as e:
        print(f"ERROR writing file: {e}")
        return False
    except subprocess.SubprocessError as e:
        print(f"ERROR running subprocess: {e}")
        return False


def get_release_info():
    try:
        with open('os-release.txt', 'r') as os_release:
            release_info = os_release.readlines()
        for info in release_info:
            build_version = re.search(r'VERSION_ID=(\w+)', info)
            if build_version is not None:
                return build_version.group(1)
        return None
    except Exception as e:
        print(f"ERROR getting cros release info: {e}")
        return None


def publish_tast_tests(token, storage_api, filename, data_path):
    try:
        headers = {
            'Authorization': token,
        }
        data = {
            'path': data_path,
        }
        files = {
            'file': (filename, open(filename, 'rb'))
        }
        url = urljoin(storage_api, 'upload')
        resp = requests.post(url, headers=headers,
                             data=data, files=files, timeout=30)
        resp.raise_for_status()
    except Exception as e:
        print(f"ERROR uploading file to storage: {e}")
        return False
    return True


def set_up_parser():
    parser = argparse.ArgumentParser(
        description='Collect tast tests list from Chrome OS release and upload to a storage area')
    subparsers = parser.add_subparsers(
        dest="command", required=True)
    subparsers.add_parser(
        "get_tast_tests", help="Get tast list from Chrome OS release")
    publish_test_list = subparsers.add_parser(
        "publish_tast_tests", help="Upload tast tests list to storage")
    publish_test_list.add_argument(
        "--token", help="Auth token to access the storage", required=True)
    publish_test_list.add_argument(
        "--storage-api", help="API address to the storage", required=True)
    publish_test_list.add_argument("--data-path", default="tast-tracker",
                                   help="Dir to save the file in the storage. Default=tast-tracker")
    return parser


def main(argv):
    parser = set_up_parser()
    args = parser.parse_args(argv)
    build_version = get_release_info()
    if not build_version:
        return False
    filename = f'cros_R{build_version}_tests.json'
    if args.command == "get_tast_tests":
        return get_tast_tests(filename)
    if args.command == "publish_tast_tests":
        return publish_tast_tests(args.token, args.storage_api, filename, args.data_path)


if __name__ == '__main__':
    status = main(sys.argv[1:])
    sys.exit(0 if status else 1)
