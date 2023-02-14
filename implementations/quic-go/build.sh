#!/bin/bash

# Version
git rev-parse HEAD > VERSION

apt-get update && apt-get install -y wget tar git

wget https://dl.google.com/go/go1.18.linux-amd64.tar.gz && \
  tar xfz go1.18.linux-amd64.tar.gz -C / && \
  rm go1.18.linux-amd64.tar.gz

export PATH="/go/bin:${PATH}"

echo ${PATH}

git clone --branch v0.31.1 https://github.com/quic-go/quic-go.git

cp -r server_code quic-go
cp -r client_code quic-go

cd quic-go

go get -d ./...

go build -o server server_code/main.go
go build -o client client_code/main.go

cd ..
cp quic-go/server .
cp quic-go/client .

# Add all necessary files to the zip
# Do NOT remove the three scripts
zip -r artifact.zip VERSION setup-env.sh run-client.sh run-server.sh server client
