#!/bin/bash
# 
# Deactivates NIC offloading capabilities for UDP and TCP.
# See https://access.redhat.com/documentation/en-us/red_hat_enterprise_linux/6/html/performance_tuning_guide/network-nic-offloads
# for offloading types.
#
# See https://www.ibm.com/docs/en/linux-on-systems?topic=3-enabling-disabling-tcp-segmentation-offload 
# or
# man ethtool
# for how to enable/disable offloading settings

# Note: ethtool allows for name shortening: tcp-segmentation-offload = tso

# environment variables given by Interop Runner:
#   "interface": interface of this machine used to communicate with other testbed machine
INTERFACE=$(jq -r .interface /tmp/interop-variables.json)

# Activate TCP Segmentation Offload (TSO)
ethtool -K ${INTERFACE} tso on

# Activate UDP Fragmentation Offload (UFO)
# ethtool name: "udp-fragmentation-offload" or "ufo"
# ethtool -K ${INTERFACE} ufo on # Seems not to exist, just ignore error

# Activate Generic Segmentation Offload (GSO), used by TCP and UDP
ethtool -K ${INTERFACE} gso on

# Activate Large Receive Offload (LRO), used by TCP
ethtool -K ${INTERFACE} lro on

# Activate Generic Receive Offload (GRO), used by TCP and UDP
ethtool -K ${INTERFACE} gro on
