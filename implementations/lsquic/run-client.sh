#!/bin/bash

# Interop runner runscript for a lsquic client
# Currently supports the goodput test only

# ATTENTION: This script only works in a specific environment!
#   1. The $REQUESTS must contain one single URL with IPv4 address and port
#   2. The $SSLKEYLOGFILE should be a file in the $LOGS directory
#   3. To achieve a SSL keylog named "keys.log" and not "012345.keys",
#      a modified http_client binary is needed. The patch to build this
#      modified binary is in the patches folder and applied in build.sh.

NOPROTO=$(echo $REQUESTS | sed "s/https:\/\///g")
DLPATH=$(echo $NOPROTO | sed "s/^[^\/]*//g")
SERVER_URL=$(echo $NOPROTO | sed "s/\/.*//g")
SERVER_IP_OR_HOSTNAME=$(echo $NOPROTO | sed "s/:.*//g")
DOWNLOADS=${DOWNLOADS::-1}

CC_ALGO=$(jq -r '.CC_ALGO // empty' /tmp/interop-variables.json)
DELAYED_ACKS=$(jq -r '.DELAYED_ACKS // empty' /tmp/interop-variables.json)
IDLE_TIMEOUT=$(jq -r '.IDLE_TIMEOUT // empty' /tmp/interop-variables.json)
MAX_UDP_PAYLOAD=$(jq -r '.MAX_UDP_PAYLOAD // empty' /tmp/interop-variables.json)
INITIAL_MAX_DATA=$(jq -r '.INITIAL_MAX_DATA // empty' /tmp/interop-variables.json)
INITIAL_MAX_STREAM_DATA_BIDI_LOCAL=$(jq -r '.INITIAL_MAX_STREAM_DATA_BIDI_LOCAL // empty' /tmp/interop-variables.json)
INITIAL_MAX_STREAM_DATA_BIDI_REMOTE=$(jq -r '.INITIAL_MAX_STREAM_DATA_BIDI_REMOTE // empty' /tmp/interop-variables.json)
INITIAL_MAX_STREAM_DATA_UNI=$(jq -r '.INITIAL_MAX_STREAM_DATA_UNI // empty' /tmp/interop-variables.json)
INITIAL_MAX_STREAMS_BIDI=$(jq -r '.INITIAL_MAX_STREAMS_BIDI // empty' /tmp/interop-variables.json)
INITIAL_MAX_STREAMS_UNI=$(jq -r '.INITIAL_MAX_STREAMS_UNI // empty' /tmp/interop-variables.json)

if [[ $TESTCASE == "goodput" ]]; then
    # Default values for the transport parameters are the same defaults used in the lsquic implementation
    # cc_algo: https://github.com/litespeedtech/lsquic/blob/927d9cb20d051cd033804c24488eb10d36667a4b/include/lsquic.h#L697

    LSQUIC_O_FLAG="-o cc_algo=${CC_ALGO:-1} "`
		`"-o delayed_acks=${DELAYED_ACKS:-1} "`
		`"-o idle_timeout=${IDLE_TIMEOUT:-30} "`
		`"-o max_udp_payload_size_rx=${MAX_UDP_PAYLOAD:-0} "`
		`"-o init_max_data=${INITIAL_MAX_DATA:-15728640} "` # (15 * 1024 * 1024)
		`"-o init_max_stream_data_bidi_local=${INITIAL_MAX_STREAM_DATA_BIDI_LOCAL:-6291456} "` # (6 * 1024 * 1024)
		`"-o init_max_stream_data_bidi_remote=${INITIAL_MAX_STREAM_DATA_BIDI_REMOTE:-0} "`
		`"-o init_max_stream_data_uni=${INITIAL_MAX_STREAM_DATA_UNI:-32768} "` # (32 * 1024)
		`"-o init_max_streams_bidi=${INITIAL_MAX_STREAMS_BIDI:-100} "`	
		`"-o init_max_streams_uni=${INITIAL_MAX_STREAMS_UNI:-100}"

    start=$(date +%s%N)
    ./http_client \
        -p $DLPATH \
        -7 $DOWNLOADS \
        -H $SERVER_IP_OR_HOSTNAME \
        -s $SERVER_URL \
        -G $LOGS\
        $LSQUIC_O_FLAG

    end=$(date +%s%N)
    echo {\"start\": $start, \"end\": $end} > ${LOGS:-.}/time.json
else
    # Exit on unknown test with code 127
    echo "exited with code 127"
    exit 127
fi
