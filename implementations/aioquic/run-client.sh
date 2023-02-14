#!/bin/bash

start=$(date +%s%N)

# Your run client code goes here
python3 client.py

echo "client exited with code $?"

end=$(date +%s%N)
echo {\"start\": $start, \"end\": $end} > ${LOGS:-.}/time.json
