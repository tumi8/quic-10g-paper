#!/bin/bash

SCRIPTDIR=`dirname "$(readlink -f "$0")"`

${SCRIPTDIR}/server

retVal=$?
if [ $retVal -eq 127 ]; then
    echo "exited with code 127"
fi

