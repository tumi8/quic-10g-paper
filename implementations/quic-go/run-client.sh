#!/bin/bash

SCRIPTDIR=`dirname "$(readlink -f "$0")"`

start=$(date +%s%N)

${SCRIPTDIR}/client $REQUESTS

end=$(date +%s%N)
echo {\"start\": $start, \"end\": $end} > ${LOGS:-.}/time.json

retVal=$?
if [ $retVal -eq 0 ]; then
    echo "client exited with code 0"
fi
