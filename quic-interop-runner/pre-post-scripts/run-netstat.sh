#!/bin/bash

apt install -y net-tools

LOG_DIR=$(jq -r .log_dir /tmp/interop-variables.json)

# If the netstat-start.txt file does not yet exist, it is created,
# otherwise the output is saved under netstat-stop.txt. If this script
# runs more than twice, only the first and last run are saved.

# As this command cannot be bound to a specific interface, the data might
# not be accurate. In our measurements, the average error was below 1%.

# Also note that this version is usig the -u flag, so only UDP traffic
# will be considered. To make it compatible to TCP(/TLS), the flag needs
# to be replaced/removed conditionally.

if ls ${LOG_DIR}/netstat-start.txt 1> /dev/null 2>&1; then
    netstat -su > ${LOG_DIR}/netstat-stop.txt
else
    netstat -su > ${LOG_DIR}/netstat-start.txt
fi
