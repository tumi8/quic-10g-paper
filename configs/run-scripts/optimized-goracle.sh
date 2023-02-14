#!/bin/bash

UDP_BUFFER=6815744

python3 run.py \
    --config configs/optimized-goracle.yml \
    -l optimized-goracle \
    --client-implementation-params rmem_value=$UDP_BUFFER \
    --server-implementation-params rmem_value=$UDP_BUFFER
