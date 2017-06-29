#!/usr/bin/python
#
# Copyright (C) 2015, 2016, 2017 Linaro Limited
# Author: Anders Roxell <anders.roxell@linaro.org>
# Author: Matt Hart <matthew.hart@linaro.org>
# Author: Tyler Baker <tyler.baker@linaro.org>
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
import shutil
import urlparse
import xmlrpclib
import json
import ssl


def setup_job_dir(arg):
    print 'Setting up job output directory at: ' + str(arg)
    if not os.path.exists(arg):
        os.makedirs(arg)
    else:
        shutil.rmtree(arg)
        os.makedirs(arg)
    directory = arg
    print 'Done setting up job output directory'
    return directory


def write_file(file, name, directory):
    with open(os.path.join(directory, name), 'w') as f:
        f.write(file)


def write_json(name, directory, data):
    with open(os.path.join(directory, name), 'w') as f:
        json.dump(data, f, indent=4, sort_keys=True)


def load_json(json_file):
    with open(json_file, 'r') as f:
        return json.load(f)


def mkdir(directory):
    if not ensure_dir(directory):
        shutil.rmtree(directory)
        os.makedirs(directory)


def ensure_dir(directory):
    if not os.path.exists(directory):
        os.makedirs(directory)
        return True
    else:
        return False


def in_bundle_attributes(bundle_atrributes, key):
    if key in bundle_atrributes:
        return True
    else:
        return False


def validate_input(username, token, server):
    url = urlparse.urlparse(server)
    if url.path.find('RPC2') == -1:
        print "LAVA Server URL must end with /RPC2"
        exit(1)
    return url.scheme + '://' + username + ':' + token + '@' + url.netloc + url.path


def connect(url):
    try:
        print "Connecting to Server..."
        if 'https' in url:
            context = hasattr(ssl, '_create_unverified_context') and ssl._create_unverified_context() or None
            connection = xmlrpclib.ServerProxy(url, transport=xmlrpclib.SafeTransport(use_datetime=True, context=context))
        else:
            connection = xmlrpclib.ServerProxy(url)
        connection.system.listMethods()
        print "Connection Successful!"
        print "connect-to-server : pass"
        return connection
    except (xmlrpclib.ProtocolError, xmlrpclib.Fault, IOError) as e:
        print "CONNECTION ERROR!"
        print "Unable to connect to %s" % url
        print e
        print "connect-to-server : fail"
        exit(1)
