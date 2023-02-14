#!/bin/bash

UDP_BUFFER=6815744

python3 run.py \
    --config configs/offloading-off.yml \
    -l offloading-off \
    --client-implementation-params rmem_value=$UDP_BUFFER \
    --server-implementation-params rmem_value=$UDP_BUFFER

python3 run.py \
    --config configs/offloading-on.yml \
    -l offloading-on \
    --client-implementation-params rmem_value=$UDP_BUFFER \
    --server-implementation-params rmem_value=$UDP_BUFFER

python3 run.py \
    --config configs/offloading-default.yml \
    -l offloading-default \
    --client-implementation-params rmem_value=$UDP_BUFFER \
    --server-implementation-params rmem_value=$UDP_BUFFER

python3 run.py \
    --config configs/offloading-udp.yml \
    -l offloading-udp \
    --client-implementation-params rmem_value=$UDP_BUFFER \
    --server-implementation-params rmem_value=$UDP_BUFFER
