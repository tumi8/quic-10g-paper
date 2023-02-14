#!/bin/bash

set -ex

if [[ $TESTCASE != "goodput" ]]; then
    echo "exited with code 127"
    exit 127
fi;

# extract the protocol
PROTO=$(echo $REQUESTS | grep :// | sed -e's,^\(.*://\).*,\1,g')
# remove the protocol
URL=$(echo ${REQUESTS/$PROTO/})
# extract the user (if any)
USER=$(echo $URL | grep @ | cut -d@ -f1)
# extract the host and port
HOSTPORT=$(echo ${URL/$USER@/} | cut -d/ -f1)
# by request host without port
HOST=$(echo $HOSTPORT | sed -e 's,:.*,,g')
# by request - try to extract the port
PORT=$(echo $HOSTPORT | sed -e 's,^.*:,:,g' -e 's,.*:\([0-9]*\).*,\1,g' -e 's,[^0-9],,g')
# extract the path (if any)
FILES=$(echo $URL | grep / | cut -d/ -f2-)


start=$(date +%s%N)

./picoquicdemo \
    -n $HOST \
    -o $DOWNLOADS \
    $HOST \
    $PORT \
    $FILES
ret=$?

end=$(date +%s%N)
echo {\"start\": $start, \"end\": $end} > ${LOGS:-.}/time.json
