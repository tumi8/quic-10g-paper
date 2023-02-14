#!/bin/bash

apt install -y sysstat jq

LOG_DIR=$(jq -r .log_dir /tmp/interop-variables.json)
ROLE=$(jq -r .role /tmp/interop-variables.json)
IMPLEMENTATION=$(jq -r .implementation /tmp/interop-variables.json)

if [[ "${IMPLEMENTATION}" == quiche* ]]; then
    PROCESS=quiche-${ROLE}
elif [[ "${IMPLEMENTATION}" == lsquic* ]]; then
    PROCESS=http_${ROLE}
elif [[ "${IMPLEMENTATION}" == picoquic* ]]; then
    PROCESS=picoquicdemo
elif [[ "${IMPLEMENTATION}" == mvfst* ]]; then
    PROCESS=hq
elif [[ "${IMPLEMENTATION}" == tcp* ]] || [[ "${IMPLEMENTATION}" == "tls1.3" ]]; then
    if [ "${ROLE}" = "server" ]; then
	    # TCP+TLS uses renamed nginx as server
	    PROCESS=nginx-server
    else
        # TCP+TLS uses wget as client
        PROCESS=wget
    fi
else
    echo "Implementation ${IMPLEMENTATION} not supported by pidstat script"
    exit 1
fi

nohup pidstat -G ${PROCESS} 1 > ${LOG_DIR}/pidstat.txt 2> ${LOG_DIR}/pidstat-error.txt &
