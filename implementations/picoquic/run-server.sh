#!/bin/bash

set -ex

if [[ $TESTCASE != "goodput" ]]; then
    echo "exited with code 127"
    exit 127
fi

./picoquicdemo \
    -c $CERTS/cert.pem \
    -k $CERTS/priv.key \
    -p $PORT \
    -a $IP \
    -w $WWW \
    -G cubic \
    -n $SERVERNAME
ret=$?

exit $?
