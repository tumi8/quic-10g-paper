#!/bin/bash

git rev-parse HEAD > VERSION

zip -r artifact.zip \
    VERSION \
    setup-env.sh run-client.sh run-server.sh \
    site-template nginx.conf cert.pem key.pem
