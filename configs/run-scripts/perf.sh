#!/bin/bash

UDP_BUFFER=6815744

python3 run.py \
    --config configs/perf-baseline.yml \
    -l perf-baseline \
    --client-implementation-params rmem_value=$UDP_BUFFER \
    --server-implementation-params rmem_value=$UDP_BUFFER

python3 run.py \
    --config configs/perf-optimized.yml \
    -l perf-optimized \
    --client-implementation-params rmem_value=$UDP_BUFFER \
    --server-implementation-params rmem_value=$UDP_BUFFER
