#!/bin/bash

# Interop runner runscript for a mvfst server
# Currently supports the goodput test only

if [[ $TESTCASE == "goodput" ]]; then

    # Based on GitHub: lnicco/mvfst-qns
    ./hq \
        --mode=server \
        --cert=${CERTS}/cert.pem \
        --key=${CERTS}/priv.key \
        --host=${IP} \
        --port=${PORT} \
        --static_root=${WWW} \
        --logdir=${LOGS} \
        --qlogger_path=${QLOGDIR}
else
    # Exit on unknown test with code 127
    echo "exited with code 127"
    exit 127
fi
