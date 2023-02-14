#!/bin/bash

set -ex

# Version
git rev-parse HEAD > VERSION

# Variables

PICOQUIC_VERSION=ec4b9263e89b9a9fe3af38885565f5b10c948e3b
PICOQUIC_REPO=https://github.com/private-octopus/picoquic.git
PICOQUIC_PATH=picoquic

PICOTLS_VERSION=33a52bbbaf97d4343eb4c346cd065595939b0238
PICOTLS_REPO=https://github.com/h2o/picotls.git
PICOTLS_PATH=picotls


# Install requirements

## picotls

apt update
apt install -y cmake pkg-config build-essential zip openssl libssl-dev

git clone $PICOTLS_REPO $PICOTLS_PATH
pushd $PICOTLS_PATH
git checkout $PICOTLS_VERSION

git submodule init
git submodule update

cmake .
make -j
# make check

popd

## picoquic

git clone $PICOQUIC_REPO $PICOQUIC_PATH
pushd $PICOQUIC_PATH
git checkout $PICOQUIC_VERSION

cmake .
make -j

# Run tests
# ./picoquic_ct

popd

# Export artifacts

cp $PICOQUIC_PATH/picoquicdemo .

zip artifact.zip \
    VERSION \
    setup-env.sh run-client.sh run-server.sh \
    picoquicdemo
