#!/bin/bash

git rev-parse HEAD > VERSION

# Nothing to build for python
# only move files to root

cp src/*.py .

zip -r artifact.zip \
    requirements.txt \
    VERSION \
    setup-env.sh run-client.sh run-server.sh \
    *.py
