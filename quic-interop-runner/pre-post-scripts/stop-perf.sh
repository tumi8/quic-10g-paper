#!/bin/bash

LOG_DIR=$(jq -r .log_dir /tmp/interop-variables.json)

# kill perf
pkill -f perf

# wait until perf has saved all files
sleep 3

# There might be problems on finding correct kernel symbols when "perf report/script" runs
# on a different kernel. Therefore it is done here and the perf.data is deleted afterwards.
perf script -i ${LOG_DIR}/perf.data > ${LOG_DIR}/out.perf
rm ${LOG_DIR}/perf.data
