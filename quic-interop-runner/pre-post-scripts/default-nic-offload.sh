#!/bin/bash

# environment variables given by Interop Runner:
#   "interface": interface of this machine used to communicate with other testbed machine
INTERFACE=$(jq -r .interface /tmp/interop-variables.json)

# TCP Segmentation Offload (TSO)
ethtool -K ${INTERFACE} tso on

# Generic Segmentation Offload (GSO), used by TCP and UDP
ethtool -K ${INTERFACE} gso on

# Large Receive Offload (LRO), used by TCP
ethtool -K ${INTERFACE} lro off

# Generic Receive Offload (GRO), used by TCP and UDP
ethtool -K ${INTERFACE} gro on
