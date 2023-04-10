#!/usr/bin/env bash
let tries=10

if [ -z "$*" ] ; then
    echo "Need to specify ssh options"
    exit 1
fi

while [[ $tries -ne 0 ]] ; do
    ssh $*
    retcode=$?
    if [[ $retcode -eq 0 ]] ; then
        break
    else
        echo "Failed, retrying..."
        sleep 1
    fi
    let tries--
done

if [[ $retcode -ne 0 ]] ; then
    echo "Connection to $* failed, giving up"
    exit 1
fi
