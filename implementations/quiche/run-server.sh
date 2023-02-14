#!/bin/bash
# Interop runner runscript for a quiche server
# Currently supports the goodput test only

# Parse server environment variables:
# - SSLKEYLOGFILE
# - QLOGDIR
# - LOGS
# - TESTCASE
# - WWW
# - CERTS
# - IP
# - PORT

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

# WWW is given as '/tmp/www_123/'
# Removing last slash for quiche
WWW=${WWW::-1}

if [[ $TESTCASE == "goodput" ]]; then
    ./quiche-server \
        --cc-algorithm cubic \
        --name "quiche-interop" \
        --listen "${IP}:${PORT}" \
        --root $WWW \
        --no-retry \
        --cert $CERTS/cert.pem \
        --key $CERTS/priv.key \
        --max-data $MAX_DATA \
        --max-window $MAX_WINDOW \
        --max-stream-data $MAX_STREAM_DATA \
        --max-stream-window $MAX_STREAM_WINDOW
else
    # Exit on unknown test with code 127
    echo "exited with code 127"
    exit 127
fi
