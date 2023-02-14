#!/bin/bash

apt install -y sysstat

LOG_DIR=$(jq -r .log_dir /tmp/interop-variables.json)

mpstat -P ALL 1 > ${LOG_DIR}/mpstat_cpu_util.txt &
