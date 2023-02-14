#!/bin/bash

sysctl -w net.core.rmem_max=212992
sysctl -w net.core.rmem_default=212992
sysctl -w net.core.wmem_max=212992
sysctl -w net.core.wmem_default=212992