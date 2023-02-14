#!/bin/bash

# Version
git rev-parse HEAD > VERSION

# Variables
PROXYGEN_REPO=https://github.com/facebook/proxygen.git
PROXYGEN_COMMIT=12d01a3f761d8aea459e4b8fbe978f9f61d231a3

apt-get update -y && apt-get upgrade -y

# Sudo is required to build mvfst 
apt-get install sudo -y

# Using proxygen to test mvfst
git clone --recursive $PROXYGEN_REPO
cd proxygen/proxygen
git checkout $PROXYGEN_COMMIT
./build.sh --with-quic --no-tests
cd ..
cd ..

# Export artifacts

cp proxygen/proxygen/_build/proxygen/httpserver/hq .
zip artifact.zip \
    VERSION \
    setup-env.sh run-client.sh run-server.sh \
    hq
