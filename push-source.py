#!/usr/bin/python
#
# Copyright (C) 2017 Linaro Limited
# Author: Matt Hart <matthew.hart@linaro.org>
#
# This module is free software; you can redistribute it and/or modify it under
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

import os
import argparse
import requests
from urlparse import urljoin
import time

def do_post_retry(url=None, data=None, headers=None, files=None):
    retry = True
    count = 5
    while retry and count >= 0:
        try:
            response = requests.post(url, data=data, headers=headers, files=files)
            if str(response.status_code)[:1] != "2":
                raise Exception(response.content)
            else:
                return response.content
                retry = False
        except Exception as e:
            print "ERROR: failed to publish"
            print e
            count = count - 1
            time.sleep(10)
    print "Failed to push file"
    exit(1)

parser = argparse.ArgumentParser()
parser.add_argument("--token", help="KernelCI API Token")
parser.add_argument("--tree", help="Kernel tree")
parser.add_argument("--describe", help="Kernel describe", default='')
parser.add_argument("--branch", help="Kernel branch")
parser.add_argument("--file", help="File to upload")
parser.add_argument("--api", help="KernelCI API URL", default="https://api.kernelci.org")
parser.add_argument("--publish_path", help="file path at destination")

args = vars(parser.parse_args())

artifacts = []
headers = {}
build_data = {}
headers['Authorization'] = args.get('token')

publish_path = args.get('publish_path', None)
if not publish_path:
    build_data['job'] = args.get('tree')
    build_data['kernel'] = args.get('describe', '')
    build_data['git_branch'] = args.get('branch')
    publish_path = os.path.join(build_data['job'], build_data['git_branch'], build_data['kernel'])

build_data['path'] = publish_path
build_data['file_server_resource'] = publish_path
filename = args.get('file')
artifacts.append(('file1',(filename, open(filename), 'rb')))
upload_url = urljoin(args.get('api'), '/upload')
print("pushing %s to %s/%s" % (filename, upload_url, publish_path))
publish_response = do_post_retry(url=upload_url, data=build_data, headers=headers, files=artifacts)
