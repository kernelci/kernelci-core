#!/usr/bin/env python3
# -*- coding:utf-8 -*
#

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

