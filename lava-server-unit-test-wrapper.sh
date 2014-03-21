#!/bin/bash
# Usage ./lava-server-unit-test-wrapper.sh

sudo su
. /srv/lava/instances/lavabot/bin/activate
python lava-server-unit-tests.py