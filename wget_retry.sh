#!/bin/bash

RETRIES=10
SLEEPTIME=5
COUNT=0
while [ $COUNT -lt $RETRIES ]
do
    wget --no-hsts --progress=dot:giga --retry-connrefused --waitretry=5 --read-timeout=20 --timeout=15 --tries 20 --continue "$@"
    if [ $? == 0 ]
    then
        exit 0
    else
        COUNT=$((COUNT + 1))
        sleep $SLEEPTIME
    fi
done
exit 1