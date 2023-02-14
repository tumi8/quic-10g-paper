#!/bin/bash
# Interop runner runscript for a quiche client
# Currently supports the goodput test only

# Parse client environment variables:
# - SSLKEYLOGFILE
# - QLOGDIR
# - LOGS
# - TESTCASE
# - DOWNLOADS
# - REQUESTS

MAX_DATA=$(jq -er '.MAX_DATA // empty'  /tmp/interop-variables.json)
MAX_WINDOW=$(jq -er '.MAX_WINDOW // empty'  /tmp/interop-variables.json)
MAX_STREAM_DATA=$(jq -er '.MAX_STREAM_DATA // empty'  /tmp/interop-variables.json)
MAX_STREAM_WINDOW=$(jq -er '.MAX_STREAM_WINDOW // empty'  /tmp/interop-variables.json)
# Default values defined in https://github.com/cloudflare/quiche/blob/master/apps/src/args.rs#L216

if [[ $? != 0 ]]; then
    MAX_DATA=10000000
    MAX_WINDOW=25165824
    MAX_STREAM_DATA=1000000
    MAX_STREAM_WINDOW=16777216
fi


if [[ $TESTCASE == "goodput" ]]; then

    # Handle empty request for compliance
    if [ -z ${REQUESTS+x} ]; then
        # unset
        exit 0
    else
        start=$(date +%s%N)
        ./quiche-client \
            --no-verify \
            --cc-algorithm cubic \
            --wire-version 00000001 \
            --dump-responses $DOWNLOADS \
            --max-data $MAX_DATA \
            --max-window $MAX_WINDOW \
            --max-stream-data $MAX_STREAM_DATA \
            --max-stream-window $MAX_STREAM_WINDOW \
            $REQUESTS
        end=$(date +%s%N)
        echo {\"start\": $start, \"end\": $end} > ${LOGS:-.}/time.json
    fi

    # on error the client exits on code 101, change to 1
    retVal=$?
    if [ $retVal -eq 101 ]; then
        exit 1
    fi
else
    # Exit on unknown test with code 127
    echo "exited with code 127"
    exit 127
fi
