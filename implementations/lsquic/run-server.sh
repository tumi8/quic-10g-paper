#!/bin/bash

# Interop runner runscript for a lsquic server
# Currently supports the goodput test only

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
		`"-o init_max_data=${INITIAL_MAX_DATA:-1572864} "` # (3 * 1024 * 1024 / 2)
		`"-o init_max_stream_data_bidi_local=${INITIAL_MAX_STREAM_DATA_BIDI_LOCAL:-0} "`
		`"-o init_max_stream_data_bidi_remote=${INITIAL_MAX_STREAM_DATA_BIDI_REMOTE:-1048576} "` # (1 * 1024 * 1024)
		`"-o init_max_stream_data_uni=${INITIAL_MAX_STREAM_DATA_UNI:-12288} "` # (12 * 1024)
		`"-o init_max_streams_bidi=${INITIAL_MAX_STREAMS_BIDI:-100} "`	
		`"-o init_max_streams_uni=${INITIAL_MAX_STREAMS_UNI:-3}"
    ./http_server \
        -s $IP:$PORT \
        -r $WWW \
        -c $SERVERNAME,$CERTS/cert.pem,$CERTS/priv.key \
        -G $LOGS \
        $LSQUIC_O_FLAG
else
    # Exit on unknown test with code 127
    echo "exited with code 127"
    exit 127
fi
