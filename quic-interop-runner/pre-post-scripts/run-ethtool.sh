#!/bin/bash

apt install -y ethtool

INTERFACE=$(jq -r .interface /tmp/interop-variables.json)
LOG_DIR=$(jq -r .log_dir /tmp/interop-variables.json)

# If the ethtool-start.txt file does not yet exist, it is created,
# otherwise the output is saved under ethtool-stop.txt. If this script
# runs more than twice, only the first and last run are saved.

if ls ${LOG_DIR}/ethtool-start.txt 1> /dev/null 2>&1; then
    ethtool -S ${INTERFACE} > ${LOG_DIR}/ethtool-stop.txt
else
    ethtool -S ${INTERFACE} > ${LOG_DIR}/ethtool-start.txt
fi
