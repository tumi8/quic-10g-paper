#!/bin/bash

apt install -y linux-perf

LOG_DIR=$(jq -r .log_dir /tmp/interop-variables.json)
ROLE=$(jq -r .role /tmp/interop-variables.json)
IMPLEMENTATION=$(jq -r .implementation /tmp/interop-variables.json)

# odd frequency "to avoid accidentally sampling in lockstep with some periodic activity, which would produce skewed results"
# source: https://www.brendangregg.com/perf.html#TimedProfiling
PERF_FREQUENCY=1997

perf record -a -g -F ${PERF_FREQUENCY} -o ${LOG_DIR}/perf.data &
