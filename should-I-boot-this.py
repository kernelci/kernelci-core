#!/usr/bin/env python3
# -*- coding:utf-8 -*
#
# Copyright (C) 2017 Free Electrons SAS
# Author: Florent Jacquet <florent.jacquet@free-electrons.com>
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
import sys
import configparser

"""
To test the script, just export those variables and play with their values

export LAB=lab-free-electrons
export TREE=mainline
"""

config = configparser.ConfigParser()
config.read('labs.ini')

# Is the lab existing?
if os.environ['LAB'] not in config.sections():
    print("Unknown lab (%s). Allowing boot of %s." % (os.environ['LAB'], os.environ['TREE']))
    sys.exit(0)

# Is the tree blacklisted for this lab?
if os.environ['TREE'] in config[os.environ['LAB']]['tree_blacklist'].split():
    print("Tree '%s' is blacklisted for lab '%s'" % (os.environ['TREE'], os.environ['LAB']))
    sys.exit(1)

print("Booting tree '%s' is allowed for lab '%s'" % (os.environ['TREE'], os.environ['LAB']))
sys.exit(0)

