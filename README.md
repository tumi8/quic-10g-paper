# QUIC on the Highway: Evaluating Performance on High Rate Links
This repository contains an adaptation of the [QUIC Interop Runner](https://github.com/marten-seemann/quic-interop-runner) that allows a performance evaluation of QUIC implementations on real hardware without the virtualization of Docker.

## Framework
The framework directory contains the adpated QUIC Interop Runner. This adaptation supports all test cases originally specified but focuses on goodput measurements with different scenarios and host configurations.
It is designed to use two servers for the client and server respectively to evaluate the influence of the system, used kernel and NIC on the goodput.

## Analysis Pipeline
The given analysis pipeline parses and formats the results of individual measurements and combines the output.
The pipeline automates the parsing of different formats, e.g., the collected perf output, but also netstat and ethtool result.

## Implementations
The implementations directory contains all testes implementations and their adaptations.

## Configurations
The configurations directory contains the configurations for all conducted measurements.
They allow to reproduce the given results and can be used as a foundation for future research.

## Results
The results directory contains all measurements conducted for the the submitted paper.
Jupyter notebooks are provided which parse the data and generate plots.
Each figure in the paper can be reproduced based on the given information.

## Used Hardware
In the Interop Runner directory, example configurations for testbed setups are provided.
The host configurations map to Figure 9 in the paper as follows:

| server-client pair    | Label    | CPU                    |
| --------------------- | -------- | ---------------------- |
| goracle-gard          | AMD-2    | AMD EPYC 7543          |
| amdexp0-amdexp1       | AMD-1    | AMD EPYC 7551P         |
| dogecoin-dogecoingold | Intel-1  | Intel Xeon CPU D-1518  |
| uniswap-solana        | Intel-2  | Intel Xeon CPU E5-1650 |
| tinyman-zone          | Intel-3  | Intel Xeon Gold 6312U  |

