#!/bin/bash
# Interop runner runscript for a TCP+TLS server
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

# WWW is given as '/tmp/www_123/'
# Removing last slash for quiche
WWW=${WWW::-1}

# Get cipher from interop runner
CIPHER=$(jq -r 'cipher // empty' /tmp/interop-variables.json)

if [[ $TESTCASE == "goodput" ]]; then
    envsubst '${IP}, ${PORT}, ${WWW}, ${CERTS}' < site-template > /etc/nginx/sites-enabled/default

    export CIPHER=${CIPHER:=TLS_AES_128_GCM_SHA256}
    envsubst '${CIPHER}' < nginx.conf > /etc/nginx/nginx.conf

    # Foreground mode using a modified default config
    # Note: renamed binary in setup-env.sh
    nginx-server

else
    # Exit on unknown test with code 127
    echo "exited with code 127"
    exit 127
fi
