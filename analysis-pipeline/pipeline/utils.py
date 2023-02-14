import os
import sys
import itertools
import configparser
import argparse

CONFIG_FILE = "pipeline.ini"

class COLORS:
    RED = "\033[31m"
    GREEN = "\033[32m"
    RESET = "\033[0m"
    UNDERLINE = "\033[4m"


def log_info(text, indentation_level=0, style=""):
    indentation = " " * 2 * indentation_level
    print(indentation + style + text + COLORS.RESET)

def log_task(text, indentation_level=0, success=False):
    indentation = " " * 2 * indentation_level
    prefix = COLORS.GREEN + "✓ " if success else COLORS.RED + "✗ "
    print(indentation + prefix  + COLORS.RESET + text)

def fail(msg):
    print(COLORS.RED + msg)
    sys.exit(1)

def load_config():
    config = configparser.ConfigParser()
    config.sections()
    p = CONFIG_FILE
    try:
        with open(p) as fp:
            config.read_file(itertools.chain(["[global]"], fp), p)
    except FileNotFoundError:
        fail(f"Config file could not be opened! Please make sure that {p} exists in this directory. You can copy the default config for quick start.")
    try:
        global RESULTS_DIR
        global FLAMEGRAPH_DIR 
        RESULTS_DIR = config["global"]["RESULTS_DIR"]
        FLAMEGRAPH_DIR = config["global"]["FLAMEGRAPH_DIR"]
    except KeyError as e:
        fail(f"Config file missing key {e}, exiting...")
    if not os.path.isdir(RESULTS_DIR):
        fail("RESULTS_DIR is not a directory")
    if not os.path.isdir(FLAMEGRAPH_DIR):
        fail("FLAMEGRAPH_DIR is not a directory")

def parse_args(args):
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "-c", "--config-file", help="config file",
        default="pipeline.ini", metavar="FILE"
    )

    parser.add_argument(
        "-d", "--log-dir", help="The log dir to process, for example logs_2022-01-01T12:00:00.",
        metavar="DIR"
    )

    parser.add_argument(
        "-a", "--all-log-dirs", help="Process all log dirs present in the results dir. This might take a long time.",
        action="store_true"
    )

    parser.add_argument(
        "-r", "--all-repetitions", help="Process repetitions instead of just the first one. This might take longer.",
        action="store_true"
    )

    parsed = parser.parse_args(args)

    global CONFIG_FILE
    CONFIG_FILE = parsed.config_file

    return parsed
