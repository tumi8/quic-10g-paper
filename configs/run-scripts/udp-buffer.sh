#!/bin/bash

# UDP Buffers (CUBIC only, maybe BBR also later?)

# default 212992B

declare -a buffersizes=(
    106496
    212992
    425984
    851968
    1703936
    3407872
    6815744
)

for i in "${buffersizes[@]}"
do
    python3 run.py \
        --config configs/udp-buffer.yml \
        -l udp-buffer-$i \
        --client-implementation-params rmem_value=$i \
        --server-implementation-params rmem_value=$i
done




