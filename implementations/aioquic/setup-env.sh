#!/bin/bash

# Your setup environment code goes here
apt update -yqqq
apt install -y git libssl-dev python3 python3-dev python3-pip
apt install -y bsd-compat-headers libffi-dev

pip3 install -r requirements.txt