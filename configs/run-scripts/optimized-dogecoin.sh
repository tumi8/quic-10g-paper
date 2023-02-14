#!/bin/bash

UDP_BUFFER=6815744

python3 run.py \
    --config configs/optimized-dogecoin.yml \
    -l optimized-dogecoin \
    --client-implementation-params rmem_value=$UDP_BUFFER \
    --server-implementation-params rmem_value=$UDP_BUFFER
