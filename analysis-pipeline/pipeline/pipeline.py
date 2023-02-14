#!/usr/bin/env python3
 
import os
import sys
import json
import enquiries

import matplotlib.pyplot as plt
import numpy as np

from tasks import FoldStacks, GenerateFlamegraph, TrimPerf
from utils import parse_args, load_config, log_info, fail, COLORS


def print_metadata(path):
    f = open(path)
    data = json.load(f)

    log_info(f"METADATA: (Server: {data['server_node_name']}, Client: {data['client_node_name']})")

    f.close()

def main(args):
    print("\nQUIC Interop Runner - Postprocessing Pipeline\n")

    parsed = parse_args(args)

    load_config()
    from utils import RESULTS_DIR, FLAMEGRAPH_DIR

    log_directories = sorted(
        list(filter(lambda x: x.startswith("logs_"), os.listdir(RESULTS_DIR))),
        reverse=True
    )
    choice = []
    if parsed.all_log_dirs:
        choice = log_directories
    elif parsed.log_dir:
        if not os.path.isdir(os.path.join(RESULTS_DIR, parsed.log_dir)):
            fail(f"log directory {parsed.log_dir} not found in {RESULTS_DIR}")
        choice = [parsed.log_dir]
    else:
        print("No command line paramters received, starting interactive mode...\n")
        choice = enquiries.choose(
            "Use SPACE to select all folders you want to process:",
            log_directories,
            multi=True,
        )

    for c in choice:
        log_info(f"Directory {c}", 0, COLORS.UNDERLINE)
        print_metadata(os.path.join(RESULTS_DIR, c, "result.json"))
        server_client = os.scandir(os.path.join(RESULTS_DIR, c))
        server_client = sorted(list(filter(lambda x: x.is_dir(), server_client)), key=lambda x: x.name)
        for sc in server_client:
            server, client = sc.name.split("_", 1)
            log_info(f"Server {server}, Client {client}", 1)
            testcases = os.scandir(sc.path)
            testcases = list(filter((lambda x: x.is_dir() and not x.name.startswith(".")), testcases))
            for testcase in testcases:
                log_info(f"Testcase {testcase.name}", 2)
                repetitions = os.scandir(testcase.path)
                repetitions = list(filter((lambda x: x.is_dir() and not x.name.startswith(".")), repetitions))
                repetitions = sorted(repetitions, key=(lambda x: x.name))
                if not parsed.all_repetitions:
                    repetitions = repetitions[:1]
                for rep in repetitions:
                    log_info(f"Repetition {rep.name}", 3)

                    params_general={
                            "dir": rep.path
                        }
                    params_client={
                            "dir": os.path.join(rep.path, "client"),
                            "suffix": "client",
                            "FLAMEGRAPH_DIR": FLAMEGRAPH_DIR
                        }
                    params_server={
                            "dir": os.path.join(rep.path, "server"),
                            "suffix": "server",
                            "FLAMEGRAPH_DIR": FLAMEGRAPH_DIR
                        }


                    for role in ["client", "server"]:
                        role_params = params_client if role == "client" else params_server

                        # task 1: trim perf data
                        task_1 = TrimPerf(role_params)
                        t1_status = task_1.run_and_log()
                        # task 2: fold stacks
                        if t1_status:
                            task_2 = FoldStacks(role_params)
                            t2_status = task_2.run_and_log()
                            # task 3: generate flame graph svg
                            if t2_status:
                                task_3 = GenerateFlamegraph(role_params)
                                task_3.run_and_log()

    print("\nDone ☺\n")


if __name__ == "__main__":
    main(sys.argv[1:])
