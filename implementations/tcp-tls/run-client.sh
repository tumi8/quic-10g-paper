#!/bin/bash
# Interop runner runscript for a TCP+TLS client in form of wget
# Currently supports the goodput test only

# Parse client environment variables:
# - SSLKEYLOGFILE
# - QLOGDIR
# - LOGS
# - TESTCASE
# - DOWNLOADS
# - REQUESTS

if [[ $TESTCASE == "goodput" ]]; then

    # Handle empty request for compliance
    if [ -z ${REQUESTS+x} ]; then
        # unset
        exit 0
    else

    start=$(date +%s%N)
	wget \
	    --quiet \
	    --no-check-certificate \
	    --directory-prefix=${DOWNLOADS} \
	    ${REQUESTS}
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
