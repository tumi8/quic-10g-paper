#!/bin/bash

# dependencies needed by mvfst
apt-get install -y           \
    libboost-all-dev         \
    libevent-dev             \
    libdouble-conversion-dev \
    libgoogle-glog-dev       \
    libgflags-dev            \
    libiberty-dev            \
    liblz4-dev               \
    liblzma-dev              \
    libsnappy-dev            \
    zlib1g-dev               \
    libjemalloc-dev          \
    libssl-dev               \
    pkg-config               \
    libsodium-dev
