#!/bin/bash

# Check arguments
if test "$#" -ne 1; then
	echo "Usage: $0 <testbed-config.json>"
	exit 1
fi

# Variables
CONFIG=$1

# Duration of the allocation in minutes
DURATION=300
SUBNET="/24"

SERVER=$(jq -r .server.host $CONFIG)
SERVER_INTERFACE=$(jq -r .server.interface $CONFIG)
SERVER_IP=$(jq -r .server.ip $CONFIG)

CLIENT=$(jq -r .client.host $CONFIG)
CLIENT_INTERFACE=$(jq -r .client.interface $CONFIG)
CLIENT_IP=$(jq -r .client.ip $CONFIG)

echo "Client: $CLIENT"
echo "Server: $SERVER"

# Print commands and exit script if one command fails
set -ex


# setup interfaces
ssh $SERVER ip a add $SERVER_IP$SUBNET dev $SERVER_INTERFACE
ssh $SERVER ip link set $SERVER_INTERFACE up

ssh $CLIENT ip a add $CLIENT_IP$SUBNET dev $CLIENT_INTERFACE
ssh $CLIENT ip link set $CLIENT_INTERFACE up

# install packages required for measurements
ssh $SERVER apt update -y
ssh $SERVER apt install -y python3-pip python3-venv ifstat linux-perf ethtool jq

ssh $CLIENT apt update -y
ssh $CLIENT apt install -y python3-pip python3-venv ifstat linux-perf ethtool jq

# Setup hosts file
ssh $CLIENT bash -c "echo $SERVER_IP server >> /etc/hosts"

