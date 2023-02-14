#!/bin/bash

# Variables

QUICHE_REPO=https://github.com/cloudflare/quiche.git
QUICHE_COMMIT=95af1427ba7aa5a96bd9b809a770747e4750971f
RUST_PLATFORM=x86_64-unknown-linux-gnu

# Version
git rev-parse HEAD > VERSION

# Rust
curl --proto '=https' --tlsv1.2 -sSf -o /tmp/rustup-init.sh https://sh.rustup.rs
chmod +x /tmp/rustup-init.sh
/tmp/rustup-init.sh -q -y --default-host $RUST_PLATFORM --default-toolchain stable --profile default
source $HOME/.cargo/env

# Quiche
git clone --recursive $QUICHE_REPO
cd quiche
cd quiche/deps/boringssl
git apply ../../../../only_aes.patch
cd ../../../
git checkout $QUICHE_COMMIT
cargo build --release
cd ..

# Export as archive
cp quiche/target/release/quiche-client .
cp quiche/target/release/quiche-server .
zip artifact.zip \
    VERSION \
    setup-env.sh run-client.sh run-server.sh \
    quiche-client \
    quiche-server
