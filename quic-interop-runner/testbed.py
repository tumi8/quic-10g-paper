import os
import abc
import json
import tempfile
import subprocess
import logging
from termcolor import colored


# This file contains the TestbedManagement class, which is used to abstract
# different testbed management systems we use. The SELECTED constant at the
# end of the file is used to select which testbed management system to use.


# FIXME: merge the function with the one in interop
def log_process(stdout, stderr, name):
    if stdout:
        logging.debug(colored(f"{name} stdout", 'yellow'))
        logging.debug(stdout.decode("utf-8"))
    if stderr:
        logging.debug(colored(f"{name} stderr", 'yellow'))
        logging.debug(stderr.decode("utf-8"))


class TestbedManagement(abc.ABC):
    logger = None

    def __init__(
        self,
        logger = None,
    ):
        self.logger = logger

    @abc.abstractmethod
    def _is_supported(self):
        pass

    @abc.abstractmethod
    def _does_remote_file_exist(self, host, path):
        pass

    @abc.abstractmethod
    def _run_script_on_machine(self, host: str, script_path: str):
        pass

    @abc.abstractmethod
    def _run_command_on_machine(self, host: str, command: list):
        pass

    @abc.abstractmethod
    def _set_variables_on_machine(self, host: str, dictionary: dict):
        pass

    @abc.abstractmethod
    def _remove_all_variables_from_machine(self, host: str):
        pass


class SimpleTestbedManagement(TestbedManagement):
    def __init__(
        self,
        logger = None,
    ):
        self.logger = logger

    def _is_supported(self):
        return True

    def _does_remote_file_exist(self, host, path):
        self.logger.debug(f"Checking if file {path} exists on {host}")

        check = subprocess.Popen(
            f'ssh {host} "test -f {path}"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )

        try:
            exit_code = check.wait(timeout=10)
            return exit_code == 0
        except subprocess.TimeoutExpired:
            return False

    def _run_command_on_machine(self, host: str, command: list):
        command_string = " ".join(command)
        self.logger.debug(f"Running command \"{command_string}\" on {host}")
        proc = subprocess.Popen(
            f'ssh {host} "{command_string}"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()
        log_process(stdout, stderr, f'host: {command}')
        return

    def _run_script_on_machine(self, host: str, script_path: str):
        self.logger.debug(f'Running {script_path} on {host}')
        proc = subprocess.Popen(
            f'ssh {host} "bash -s" -- < {script_path}',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = proc.communicate()
        log_process(stdout, stderr, f'host: {script_path}')
        return

    def _set_variables_on_machine(self, host: str, dictionary: dict):
        self.logger.debug(f"Setting the variables:\n{dictionary}\non the host {host}")

        tmp_file = tempfile.NamedTemporaryFile(dir="/tmp", prefix="interop-temp-data-", mode="w+")
        json.dump(dictionary, tmp_file, ensure_ascii=False, indent=4)
        tmp_file.flush()
        tmp_file.seek(0)

        src = tmp_file.name
        dst = "/tmp/interop-variables.json"
        self.logger.debug(f"Copy {src} to {host}:{dst}")
        cmd = f'rsync -r {src} {host}:{dst}'

        p = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            p.wait(10)
        except subprocess.TimeoutExpired:
            self.logger.debug(
                f'Timeout when moving variable file to host {host}')
        finally:
            tmp_file.close()
            return

    def _remove_all_variables_from_machine(self, host: str):
        self.logger.debug(f"Removing all variables from {host}")
        prog = subprocess.Popen(
            f'ssh {host} "rm -rf /tmp/interop-variables.json"',
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        return prog.wait(10)

SELECTED = SimpleTestbedManagement
