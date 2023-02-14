#!/bin/bash

LOG_DIR=$(jq -r .log_dir /tmp/interop-variables.json)
INTERFACE=$(jq -r .interface /tmp/interop-variables.json)

tc -s -d qdisc show dev ${INTERFACE} > ${LOG_DIR}/tc-stats.txt
