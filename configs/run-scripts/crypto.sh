#!/bin/bash

UDP_BUFFER=6815744

AES=TLS_AES_128_GCM_SHA256
CHACHA=TLS_CHACHA20_POLY1305_SHA256

python3 run.py \
    --config configs/crypto.yml \
    -l crypto/aes-ni \
    --client-implementation-params rmem_value=$UDP_BUFFER cipher=$AES \
    --server-implementation-params rmem_value=$UDP_BUFFER cipher=$AES

python3 run.py \
    --config configs/crypto.yml \
    -l crypto/aes-noni \
    -c lsquic,quiche,tls1.3 \
    -s lsquic,quiche,tls1.3 \
    --disable-server-aes-offload \
    --disable-client-aes-offload \
    --client-implementation-params rmem_value=$UDP_BUFFER cipher=$AES \
    --server-implementation-params rmem_value=$UDP_BUFFER cipher=$AES

python3 run.py \
    --config configs/crypto.yml \
    -l crypto/chacha20 \
    --client-implementation-params rmem_value=$UDP_BUFFER cipher=$CHACHA \
    --server-implementation-params rmem_value=$UDP_BUFFER cipher=$CHACHA




