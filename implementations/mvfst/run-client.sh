#!/bin/bash

# Interop runner runscript for a mvfst client
# Currently supports the goodput test only

if [[ $TESTCASE == "goodput" ]]; then

    # Handle empty request for compliance
    if [ -z ${REQUESTS+x} ]; then
        # unset
        exit 0
    else

        # Based on GitHub: lnicco/mvfst-qns
        INVOCATIONS=$(echo ${REQUESTS} | tr " " "\n" | awk -F '/' '{ print "/" $4 }' | paste -sd',')
        REQS=($REQUESTS)
        REQ=${REQS[0]}
        SERVER=$(echo $REQ | cut -d'/' -f3 | cut -d':' -f1)
        PORT=$(echo $REQ | cut -d':' -f3 | cut -d'/' -f1)

        start=$(date +%s%N)

        for INVOCATION in ${INVOCATIONS}; do

          echo "requesting files '${INVOCATION}'"
          ./hq \
              --mode=client \
              --host=${SERVER} \
              --port=${PORT} \
              --quic-version=1 \
              --path="${INVOCATION}" \
              --outdir=${DOWNLOADS} \
              --logdir=${LOGS} \
              --qlogger_path=${QLOGDIR}
      done
      end=$(date +%s%N)
      echo {\"start\": $start, \"end\": $end} > ${LOGS:-.}/time.json
    fi
else
    # Exit on unknown test with code 127
    echo "exited with code 127"
    exit 127
fi
