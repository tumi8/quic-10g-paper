#!/bin/bash

# Version
git rev-parse HEAD > VERSION

# Variables

BORINGSSL_COMMIT=a9670a8b476470e6f874fef3554e8059683e1413
LSQUIC_COMMIT=f3657f1f27e79dd56587e880abe95426469625b0
GO_DOWNLOAD_FILENAME=go1.18.3.linux-amd64.tar.gz

# Install requirements
# (go and boringssl could be added to build container)

apt-get update && \
apt-get install -y build-essential git cmake software-properties-common \
                zlib1g-dev libevent-dev wget

wget https://golang.org/dl/$GO_DOWNLOAD_FILENAME
tar -zxvf $GO_DOWNLOAD_FILENAME -C /usr/local/

echo "export PATH=/usr/local/go/bin:${PATH}" | tee /etc/profile.d/go.sh
source /etc/profile.d/go.sh

mkdir build && cd build

git clone https://boringssl.googlesource.com/boringssl && \
cd boringssl && \
git checkout $BORINGSSL_COMMIT && \
cmake . && make -j && \
cd ..

# Build lsquic

git clone https://github.com/litespeedtech/lsquic.git && \
cd lsquic && \
git checkout $LSQUIC_COMMIT && \
git submodule init && git submodule update && \
git apply ../../patches/sslkeylogdir.patch && \
cmake  -DBORINGSSL_DIR=../boringssl . && \
make -j && make test && \
cd ../..

# Export artifacts

cp build/lsquic/bin/http_client .
cp build/lsquic/bin/http_server .
zip artifact.zip \
    VERSION \
    setup-env.sh run-client.sh run-server.sh \
    http_client \
    http_server
