import json
import logging
import os
import random
import re
import shutil
import statistics
import string
import subprocess
import sys
import tempfile
from datetime import datetime
from typing import Callable, List, Tuple
import pathlib

import time
import psutil

import prettytable
from termcolor import colored

import testcases
from result import TestResult
from testcases import Perspective

import venv

import testbed as testbed_management

def on_terminate(proc):
    logging.debug("process {} terminated with exit code {}".format(proc, proc.returncode))

def random_string(length: int):
    """ Generate a random string of fixed length """
    letters = string.ascii_lowercase
    return "".join(random.choice(letters) for i in range(length))


def kill(proc_pid):
    process = psutil.Process(proc_pid)
    procs = process.children(recursive=True)
    for proc in procs:
        proc.terminate()
    gone, alive = psutil.wait_procs(procs, timeout=3, callback=on_terminate)
    for p in alive:
        p.kill()
    process.terminate()

class MeasurementResult:
    result = TestResult
    details = str
    all_infos: [float] = []


class LogFileFormatter(logging.Formatter):
    def format(self, record):
        msg = super(LogFileFormatter, self).format(record)
        # remove color control characters
        return re.compile(r"\x1B[@-_][0-?]*[ -/]*[@-~]").sub("", msg)


class LogConsoleFormatter(logging.Formatter):
    pass


def log_process(stdout, stderr, name):
    if stdout:
        logging.debug(colored(f"{name} stdout", 'yellow'))
        logging.debug(stdout.decode("utf-8"))
    if stderr:
        logging.debug(colored(f"{name} stderr", 'yellow'))
        logging.debug(stderr.decode("utf-8"))


class InteropRunner:
    _start_time = 0
    test_results = {}
    measurement_results = {}
    compliant = {
        'server': {},
        'client': {}
    }
    testcase_is_unsupported = {
        'server': {},
        'client': {}
    }
    _prepared_envs = {
        'server': [],
        'client': []
    }
    _implementations = {}
    _servers = []
    _clients = []
    _tests = []
    _measurements = []
    _output = ""
    _log_dir = ""
    _save_files = False
    _venv_dir = ""
    _testbed = None
    _testbed_management = None
    _bandwidth = None
    _client_delay = None
    _server_delay = None
    _server_pre_scripts = [],
    _server_post_scripts = [],
    _client_pre_scripts = [],
    _client_post_scripts = [],
    _client_implementation_params = {},
    _server_implementation_params = {},
    _disable_server_aes_offload = False,
    _disable_client_aes_offload = False,
    _args = {},

    def __init__(
        self,
        client_implementation_params,
        server_implementation_params,
        implementations: dict,
        servers: List[str],
        clients: List[str],
        tests: List[testcases.TestCase],
        measurements: List[testcases.Measurement],
        output: str,
        debug: bool,
        save_files=False,
        log_dir="",
        venv_dir="",
        testbed=None,
        bandwidth: str=None,
        client_delay: str=None,
        server_delay: str=None,
        implementations_directory: str='.',
        server_pre_scripts: [str]=[],
        server_post_scripts: [str]=[],
        client_pre_scripts: [str]=[],
        client_post_scripts: [str]=[],
        disable_server_aes_offload = False,
        disable_client_aes_offload = False,
        continue_on_error=False,
        use_client_timestamps=False,
        only_same_implementation=False,
        args={},
    ):
        self.logger = logging.getLogger()
        self.logger.setLevel(logging.DEBUG)
        console = logging.StreamHandler(stream=sys.stderr)
        formatter = LogConsoleFormatter("%(message)s")
        console.setFormatter(formatter)
        if debug:
            console.setLevel(logging.DEBUG)
        else:
            console.setLevel(logging.INFO)
        self.logger.addHandler(console)
        self._start_time = datetime.now()
        self._tests = tests
        self._measurements = measurements
        self._servers = servers
        self._clients = clients
        self._implementations = implementations
        self._implementations_directory = implementations_directory
        self._output = output
        self._log_dir = log_dir
        self._save_files = save_files
        self._venv_dir = venv_dir
        self._testbed = testbed
        self.logger.debug(f"Running {self._testbed} {bool(self._testbed)}")
        if self._testbed:
            with open(self._testbed) as f:
                data = json.load(f)
                self._testbed_server = data['server']['host']
                self._testbed_server_ip = data['server']['ip']
                self._testbed_server_interface = data['server']['interface']
                self._testbed_client = data['client']['host']
                self._testbed_client_interface = data['client']['interface']
            self.logger.debug(f"Running in testbed mode")
            self.logger.debug(f"Server: {self._testbed_server}   Client: {self._testbed_client}")
            self._testbed = True
            self._testbed_management = testbed_management.SELECTED(logger=self.logger)
        if len(self._venv_dir) == 0:
            self._venv_dir = "/tmp"
        if len(self._log_dir) == 0:
            self._log_dir = "logs_{:%Y-%m-%dT%H:%M:%S}".format(self._start_time)
        if os.path.exists(self._log_dir):
            sys.exit("Log dir " + self._log_dir + " already exists.")
        for server in servers:
            self.test_results[server] = {}
            self.measurement_results[server] = {}
            for client in clients:
                self.test_results[server][client] = {}
                for test in self._tests:
                    self.test_results[server][client][test] = {}
                self.measurement_results[server][client] = {}
                for measurement in measurements:
                    self.measurement_results[server][client][measurement] = {}
        # tc settings
        self._bandwidth = bandwidth
        self._client_delay = client_delay
        self._server_delay = server_delay
        # pre- and postscripts of server and client
        self._server_pre_scripts = server_pre_scripts
        self._server_post_scripts = server_post_scripts
        self._client_pre_scripts = client_pre_scripts
        self._client_post_scripts = client_post_scripts
        # implementation parameters
        self._client_implementation_params = client_implementation_params
        self._server_implementation_params = server_implementation_params

        # AES offload
        self._disable_server_aes_offload = disable_server_aes_offload
        self._disable_client_aes_offload = disable_client_aes_offload
        # other
        self._continue_on_error = continue_on_error
        self._use_client_timestamps = use_client_timestamps
        self._only_same_implementation = only_same_implementation
        self._args = args

    def _is_client_or_server_solomode(self, client, server) -> bool:
        if "solo" in self._implementations[client].keys():
            return self._implementations[client]["solo"]
        elif "solo" in self._implementations[server].keys():
            return self._implementations[server]["solo"]
        else:
            return False


    def _get_node_image(self) -> str:
        p = subprocess.Popen(
            "STR=$(grep IMAGE= setup-hosts.sh);" \
            + "echo ${STR#*=}",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate(timeout=10)
        return stdout.decode("utf-8").rstrip("\n").strip("\"")
        
    def _get_commit_hash(self) -> str:
        p = subprocess.Popen(
            "git rev-parse HEAD",
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = p.communicate(timeout=10)
        return stdout.decode("utf-8").rstrip("\n")


    def _remove_server_bandwidth_limit(self):
        self.logger.debug(f'Removing server bandwidth limit')
        return self._testbed_management._run_command_on_machine(
            self._testbed_server,
            ['tc', 'qdisc', 'del', 'dev', self._testbed_server_interface, 'root']
        )

    def _set_server_bandwidth_limit(self, bandwidth: str):
        self.logger.debug(f'Limiting bandwidth on server {self._testbed_server} to {self._bandwidth}')
        return self._testbed_management._run_command_on_machine(
            self._testbed_server,
            [
                'tc', 'qdisc', 'add', 'dev', self._testbed_server_interface, 
                'root', 'tbf', 'rate', bandwidth, 'latency', '50ms', 'burst', 
                '1540'
            ]
        )

    def _remove_client_delay(self):
        self.logger.debug(f'Removing client delay')
        return self._testbed_management._run_command_on_machine(
            self._testbed_client,
            ['tc', 'qdisc', 'del', 'dev', self._testbed_client_interface, 'root']
        )

    def _set_client_delay(self, delay: str):
        self.logger.debug(f'Adding delay on client {self._testbed_client} to {self._client_delay}')
        return self._testbed_management._run_command_on_machine(
            self._testbed_client,
            [
                'tc', 'qdisc', 'add', 'dev', self._testbed_client_interface, 
                'root', 'netem', 'delay', delay, 'limit', '100000'
            ]
        )

    def _remove_server_delay(self):
        self.logger.debug(f'Removing server delay')
        return self._testbed_management._run_command_on_machine(
            self._testbed_server,
            ['tc', 'qdisc', 'del', 'dev', self._testbed_server_interface, 'root']
        )

    def _set_server_delay(self, delay: str):
        self.logger.debug(f'Adding delay on server {self._testbed_server} to {self._server_delay}')
        return self._testbed_management._run_command_on_machine(
            self._testbed_server,
            [
                'tc', 'qdisc', 'add', 'dev', self._testbed_server_interface, 
                'root', 'netem', 'delay', delay, 'limit', '100000'
            ]
        )

    def _create_venv_on_remote_host(self, host, venv_dir_path):
        self.logger.debug(f"Venv Setup: Creating venv on host {host} at \
                {venv_dir_path}")
        return self._testbed_management._run_command_on_machine(
            host,
            ['python3', '-m', 'venv', venv_dir_path]
        )

    def _get_venv(self, name, role):
        """Creates the venv directory for the specified role either locally or
        copied to the host in testbed mode should it not exist.

        Return: the path of the
         with a prepended bash 'source' command.
        """
        venv_dir = os.path.join(self._venv_dir, name + "-" + role)
        venv_activate = os.path.join(venv_dir, "bin/activate")

        if self._testbed:
            host = self._testbed_server if role == 'server' else self._testbed_client
            if not self._testbed_management._does_remote_file_exist(host, venv_activate):
                self._create_venv_on_remote_host(host, venv_dir)
        else:
            if not os.path.exists(venv_activate):
                self.logger.debug(f'Create venv: {venv_dir}')
                venv.create(venv_dir, with_pip=True)
        return ". " + venv_activate

    def get_implementation_version(self, name):
        try:
            with open(os.path.join(self._implementations_directory, self._implementations[name]['path'], 'VERSION')) as f:
                version = f.readline().rstrip('\n')
                return version
        except Exception as e:
            self.logger.error(f'Failed to ger version of {name}: {e}')
            return None

    def _copy_implementations(self):
        """
            Copies the implementations to the remote hosts, if in testbed mode.
        """
        if self._testbed:
            for client in self._clients:
                self._push_directory_to_remote(
                    self._testbed_client,
                    os.path.join(
                        self._implementations_directory,
                        self._implementations[client]['path'],
                        ''  # This prevents that rsync copies the directory into itself, adds trailing slash
                    ),
                    self._implementations[client]['path'],
                    normalize=False
                )
            for server in self._servers:
                self._push_directory_to_remote(
                    self._testbed_server,
                    os.path.join(
                        self._implementations_directory,
                        self._implementations[server]['path'],
                        ''
                    ),
                    self._implementations[server]['path'],
                    normalize=False
                )

    def _push_directory_to_remote(self, host, src, dst=None, normalize=True):
        """Copies a directory <src> from the machine it is executed on
        (management host) to a given host <host> to path <dst> using rsync.
        """
        if normalize:
            src = os.path.normpath(src)

        if not dst:
            dst = str(pathlib.Path(src).parent)
        self.logger.debug(f"Copy {src} to {host}:{dst}")

        cmd = f'rsync -r {src} {host}:{dst}'
        p = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            # large timeout as copied file could be very large
            p.wait(2000)
        except subprocess.TimeoutExpired:
            self.logger.debug(
                f'Timeout when moving files {src} to host {host}')
        return


    def _pull_directory_from_remote(self, host, src, dst=None):
        src = os.path.normpath(src)
        if not dst:
            dst = str(pathlib.Path(src).parent)
        self.logger.debug(f"Copy {host}:{src} to {dst}")

        cmd = f'rsync -r {host}:{src} {dst}'
        p = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        try:
            # large timeout as copied file could be very large
            p.wait(2000)
        except subprocess.TimeoutExpired:
            self.logger.debug(
                f'Timeout when copying files {src} from host {host}')
        return

    def _delete_remote_directory(self, host, directory):
        cmd = f'ssh {host} "rm -rf {directory}"'
        self.logger.debug(f"Deleting {host}:{directory}")

        setup_env = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )


    def _is_unsupported(self, lines: List[str]) -> bool:
        return any("exited with code 127" in str(line) for line in lines) or any(
            "exit status 127" in str(line) for line in lines
        )

    def _check_impl_is_compliant(self, name: str, role: str) -> bool:
        """ check if an implementation return UNSUPPORTED for unknown test cases """
        assert role in ['client', 'server']

        if name in self.compliant[role]:
            self.logger.debug(
                f"{name} ({role}) already tested for compliance: {str(self.compliant[role][name])}"
            )
            return self.compliant[role][name]

        log_dir = tempfile.TemporaryDirectory(dir="/tmp", prefix="logs_")
        www_dir = tempfile.TemporaryDirectory(dir="/tmp", prefix="compliance_www_")
        certs_dir = tempfile.TemporaryDirectory(dir="/tmp", prefix="compliance_certs_")
        downloads_dir = tempfile.TemporaryDirectory(
            dir="/tmp", prefix="compliance_downloads_"
        )

        run_script = self._implementations[name]['path'] + f"/run-{role}.sh"

        # Check if runscript.sh exists
        if self._testbed:
            host = self._testbed_server if role == 'server' else self._testbed_client
            if not self._testbed_management._does_remote_file_exist(host, run_script):
                self.logger.error(colored(f"{run_script} does not exist", 'red'))
                self.compliant[role][name] = False
                return False
        else:
            run_script = os.path.join(self._implementations_directory, run_script)
            if not os.path.isfile(run_script):
                self.logger.error(colored(f"{run_script} does not exist", 'red'))
                self.compliant[role][name] = False
                return False

        testcases.generate_cert_chain(certs_dir.name)

        if self._testbed:
            for dir in [log_dir.name, www_dir.name, certs_dir.name, downloads_dir.name]:
                self._push_directory_to_remote(
                    self._testbed_server if role == 'server' else self._testbed_client,
                    dir
                )

        venv_script = self._get_venv(name, role)

        params = " ".join([
            f"TESTCASE={random_string(6)}",
            f"DOWNLOADS={downloads_dir.name}",
            f"LOGS={log_dir.name}",
            f"QLOGDIR={log_dir.name}",
            f"SSLKEYLOGFILE={log_dir.name}/keys.log",
            f"IP=localhost",
            f"PORT=4433",
            f"CERTS={certs_dir.name}",
            f"WWW={www_dir.name}",
        ])
        cmd = f"{venv_script}; {params} ./run-{role}.sh"

        if self._testbed:
            cmd = f'ssh {self._testbed_server if role == "server" else self._testbed_client} \'cd {self._implementations[name]["path"]}; {cmd}\''

        self.logger.debug(cmd)

        # Do not set cwd for testbed mode
        if self._testbed:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT
            )
        else:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                cwd=os.path.join(self._implementations_directory, self._implementations[name]['path'])
            )

        try:
            stdout, stderr = proc.communicate(timeout=10)
        except subprocess.TimeoutExpired:
            self.logger.error(colored(f"{name} {role} compliance check timeout", 'red'))
            self.logger.error(colored(f"{name} {role} not compliant", 'red'))
            self.compliant[role][name] = False
            return False
        finally:
            if self._testbed:
                host = self._testbed_server if role == "server" else self._testbed_client
                self._delete_remote_directory(host, log_dir.name)
                self._delete_remote_directory(host, www_dir.name)
                self._delete_remote_directory(host, certs_dir.name)
                self._delete_remote_directory(host, downloads_dir.name)

        if not proc.returncode == 127 and not self._is_unsupported(stdout.decode("utf-8").splitlines()):
            self.logger.error(colored(f"{name} {role} not compliant", 'red'))
            self.logger.debug("%s", stdout.decode("utf-8"))
            self.compliant[role][name] = False
            return False
        self.logger.debug(f"{name} {role} compliant.")

        # remember compliance test outcome
        self.compliant[role][name] = True
        return True

    def _check_test_is_unsupported(self, name: str, role: str, testcase: str) -> bool:
        """ check if a testcase returns UNSUPPORTED """
        return testcase in self.testcase_is_unsupported[role].get(name, [])

    def _set_testcase_unsupported(self, name: str, role: str, testcase: str) -> bool:
        if not name in self.testcase_is_unsupported[role].keys():
            self.testcase_is_unsupported[role][name] = []
        self.testcase_is_unsupported[role][name].append(testcase)

    def _print_results(self):
        """print the interop table"""
        self.logger.info("\n\nRun took %s", datetime.now() - self._start_time)

        def get_letters(result):
            return ",".join(
                [test.abbreviation() for test in cell if cell[test] is result]
            )

        if len(self._tests) > 0:
            t = prettytable.PrettyTable()
            t.hrules = prettytable.ALL
            t.vrules = prettytable.ALL
            t.field_names = [""] + [name for name in self._servers]
            for client in self._clients:
                row = [client]
                for server in self._servers:
                    cell = self.test_results[server][client]
                    res = colored(get_letters(TestResult.SUCCEEDED), "green") + "\n"
                    res += colored(get_letters(TestResult.UNSUPPORTED), "yellow") + "\n"
                    res += colored(get_letters(TestResult.FAILED), "red")
                    row += [res]
                t.add_row(row)
            print("\n\u2193clients/servers\u2192")
            print(t)

        if len(self._measurements) > 0:
            t = prettytable.PrettyTable()
            t.hrules = prettytable.ALL
            t.vrules = prettytable.ALL
            t.field_names = [""] + [name for name in self._servers]
            for client in self._clients:
                row = [client]
                for server in self._servers:
                    cell = self.measurement_results[server][client]
                    results = []
                    for measurement in self._measurements:
                        res = cell[measurement]
                        if not hasattr(res, "result"):
                            continue
                        if res.result == TestResult.SUCCEEDED:
                            results.append(
                                colored(
                                    measurement.abbreviation() + ": " + res.details,
                                    "green",
                                )
                            )
                        elif res.result == TestResult.UNSUPPORTED:
                            results.append(colored(measurement.abbreviation(), "yellow"))
                        elif res.result == TestResult.FAILED:
                            results.append(colored(measurement.abbreviation(), "red"))
                    row += ["\n".join(results)]
                t.add_row(row)
            print(t)

    def _export_results(self):
        if not self._output:
            self._output = os.path.join(self._log_dir, 'result.json')
            if not os.path.exists(self._log_dir):
                os.makedirs(self._log_dir)

        self.logger.info(f'Exporting results to {self._output}')

        out = {
            "interop_commit_hash": self._get_commit_hash(),
            "interop_start_time_unix_timestamp": self._start_time.timestamp(),
            "interop_end_time_unix_timestamp": datetime.now().timestamp(),
            "log_dir": self._log_dir,
            "server_node_name": self._testbed_server if self._testbed else None,
            "client_node_name": self._testbed_client if self._testbed else None,
            "node_image": self._get_node_image()if self._testbed else None,
            "server_implementations": {name: self.get_implementation_version(name) for name in self._servers},
            "client_implementations": {name: self.get_implementation_version(name) for name in self._clients},
            "bandwidth_limit": str(self._bandwidth),
            "client_delay": str(self._client_delay),
            "server_delay": str(self._server_delay),
            "tests": {
                x.abbreviation(): {
                    "name": x.name(),
                    "desc": x.desc(),
                }
                for x in self._tests + self._measurements
            },
            "quic_draft": testcases.QUIC_DRAFT,
            "quic_version": testcases.QUIC_VERSION,
            "results": [],
            "measurements": [],
            "args": self._args,
        }

        for client in self._clients:
            for server in self._servers:
                results = []
                for test in self._tests:
                    r = None
                    if hasattr(self.test_results[server][client][test], "value"):
                        r = self.test_results[server][client][test].value
                    results.append(
                        {
                            "abbr": test.abbreviation(),
                            "name": test.name(),  # TODO: remove
                            "result": r,
                        }
                    )
                out["results"].append(results)

                measurements = []
                for measurement in self._measurements:
                    res = self.measurement_results[server][client][measurement]
                    if not hasattr(res, "result"):
                        continue
                    measurements.append(
                        {
                            "name": measurement.name(),  # TODO: remove
                            "abbr": measurement.abbreviation(),
                            "filesize": min(measurement.FILESIZE, self._get_max_filesize(client, server)) if self._get_max_filesize(client, server) is not None else measurement.FILESIZE,
                            "result": res.result.value,
                            "average": res.details,
                            "details": res.all_infos,
                            "server": server,
                            "client": client,
                        }
                    )
                out["measurements"].append(measurements)

        f = open(self._output, "w")
        json.dump(out, f)
        f.close()

        # Copy server and client pre- and postscripts into logdir root
        for server_script in self._server_pre_scripts:
            shutil.copyfile(server_script, 
                            os.path.join(self._log_dir, 'spre_' + \
                                         server_script.split("/")[1]
                                        )
            )
        for server_script in self._server_post_scripts:
            shutil.copyfile(server_script, 
                        os.path.join(self._log_dir, 'spost_' + \
                                     server_script.split("/")[1]
                                    )
        )
        for client_script in self._client_pre_scripts:
            shutil.copyfile(client_script, 
                            os.path.join(self._log_dir, 'cpre_' + \
                                         client_script.split("/")[1]
                                        )
            )
        for client_script in self._client_post_scripts:
            shutil.copyfile(client_script, 
                        os.path.join(self._log_dir, 'cpost_' + \
                                     client_script.split("/")[1]
                                    )
        )

        return

    def _run_testcase(
        self, server: str, client: str, test: Callable[[], testcases.TestCase]
    ) -> TestResult:
        return self._run_test(server, client, None, test)[0]

    def _run_test(
        self,
        server: str,
        client: str,
        log_dir_prefix: None,
        test: Callable[[], testcases.TestCase],
    ) -> Tuple[TestResult, float]:

        if self._check_test_is_unsupported(name=client, role='client', testcase=test.name()):
            self.logger.info(colored(f"Client {client} does not support {test.name()}", "red"))
            return TestResult.UNSUPPORTED, None

        if self._check_test_is_unsupported(name=server, role='server', testcase=test.name()):
            self.logger.info(colored(f"Server {server} does not support {test.name()}", "red"))
            return TestResult.UNSUPPORTED, None

        start_time = datetime.now()
        sim_log_dir = tempfile.TemporaryDirectory(dir="/tmp", prefix="logs_sim_")
        server_log_dir = tempfile.TemporaryDirectory(dir="/tmp", prefix="logs_server_")
        client_log_dir = tempfile.TemporaryDirectory(dir="/tmp", prefix="logs_client_")
        log_file = tempfile.NamedTemporaryFile(dir="/tmp", prefix="output_log_")
        log_handler = logging.FileHandler(log_file.name)
        log_handler.setLevel(logging.DEBUG)

        formatter = LogFileFormatter("%(asctime)s %(message)s")
        log_handler.setFormatter(formatter)
        self.logger.addHandler(log_handler)

        client_keylog = os.path.join(client_log_dir.name, 'keys.log')
        server_keylog = os.path.join(server_log_dir.name, 'keys.log')

        client_qlog_dir = os.path.join(client_log_dir.name, 'client_qlog/')
        server_qlog_dir = os.path.join(server_log_dir.name, 'server_qlog/')

        server_ip = '127.0.0.1'
        server_name = 'server'

        # Check if test object is of MEASUREMENTS or TESTCASES type
        # a Measurement Object has additional bandwidth parameters
        testcase = test(
            sim_log_dir=sim_log_dir,
            client_keylog_file=client_keylog,
            server_keylog_file=server_keylog,
            client_log_dir=client_log_dir.name,
            server_log_dir=server_log_dir.name,
            client_qlog_dir=client_qlog_dir,
            server_qlog_dir=server_qlog_dir,
            server_ip=server_ip if not self._testbed else self._testbed_server_ip,
            server_name=server_name,
            link_bandwidth=self._bandwidth,
            client_delay=self._client_delay,
            server_delay=self._server_delay
        )

        if self._testbed:
            for dir in [server_log_dir.name, testcase.www_dir(), testcase.certs_dir()]:
                self._push_directory_to_remote(self._testbed_server, dir)
            for dir in [sim_log_dir.name, client_log_dir.name, testcase.download_dir()]:
                self._push_directory_to_remote(self._testbed_client, dir)

        paths = testcase.get_paths(
            max_size=self._get_max_filesize(client, server),
            host=self._testbed_server if self._testbed else None
        )

        reqs = " ".join([testcase.urlprefix() + p for p in paths])
        self.logger.debug("Requests: %s", reqs)

        server_params = " ".join([
            f"SSLKEYLOGFILE={server_keylog}",
            f"QLOGDIR={server_qlog_dir}" if testcase.use_qlog() else "",
            f"LOGS={server_log_dir.name}",
            f"TESTCASE={testcase.testname(Perspective.SERVER)}",
            f"WWW={testcase.www_dir()}",
            f"CERTS={testcase.certs_dir()}",
            f"IP={testcase.ip()}",
            f"PORT={testcase.port()}",
            f"SERVERNAME={testcase.servername()}",
        ])
        if self._disable_server_aes_offload:
            server_params = " ".join([
                'OPENSSL_ia32cap="~0x200000200000000"',
                server_params
            ])

        client_params = " ".join([
            f"SSLKEYLOGFILE={client_keylog}",
            f"QLOGDIR={client_qlog_dir}" if testcase.use_qlog() else "",
            f"LOGS={client_log_dir.name}",
            f"TESTCASE={testcase.testname(Perspective.CLIENT)}",
            f"DOWNLOADS={testcase.download_dir()}",
            f"REQUESTS=\"{reqs}\"",
        ])
        if self._disable_client_aes_offload:
            client_params = " ".join([
                'OPENSSL_ia32cap="~0x200000200000000"',
                client_params
            ])

        server_run_script = "./run-server.sh"
        server_venv_script = self._get_venv(server, "server")
        client_run_script = "./run-client.sh"
        client_venv_script = self._get_venv(client, "client")

        interface = 'lo' if not sys.platform == "darwin" else 'lo0'
        interface = interface if not self._testbed else self._testbed_client_interface

        trace_cmd = f"tcpdump -i {interface} -U -w {sim_log_dir.name}/trace.pcap"
        ifstat_cmd = f"ifstat -i {interface} -bn -t > {sim_log_dir.name}/interface_status.txt"

        server_cmd = f"{server_venv_script}; {server_params} {server_run_script}"
        client_cmd = f"{client_venv_script}; {client_params} {client_run_script}"

        if self._testbed:
            trace_cmd = f'ssh {self._testbed_client} "{trace_cmd}"'
            ifstat_cmd = f'ssh {self._testbed_client} "{ifstat_cmd}"'

            server_cmd = f'ssh {self._testbed_server} \'cd {self._implementations[server]["path"]}; {server_cmd}\''
            client_cmd = f'ssh {self._testbed_client} \'cd {self._implementations[client]["path"]}; {client_cmd}\''

        expired = False
        try:
            if testcase.use_tcpdump():
                self.logger.debug(f'Starting tcpdump on {interface}')
                trace = subprocess.Popen(
                    trace_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            if testcase.use_ifstat():
                self.logger.debug(f'Starting ifstat on {interface}')
                ifstat = subprocess.Popen(
                    ifstat_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            if testcase.use_tcpdump() or testcase.use_ifstat():
                # Wait until processes are started
                time.sleep(2)

            # Limit bandwidth using tc for measurements if was set
            if self._testbed and testcase.is_bandwidth_limited():
                self._set_server_bandwidth_limit(
                    testcase.bandwidth()
                )
            # Add delay using tc for measurements if was set
            if self._testbed and testcase.is_client_delay_added():
                self._set_client_delay(
                    testcase.client_delay()
                )
            if self._testbed and testcase.is_server_delay_added():
                self._set_server_delay(
                    testcase.server_delay()
                )

            # Set client and server variables for pre and post scripts
            #
            # These have to be set every iteration as we want to offer temporary
            # log directories to the scripts as well.
            server_variables: dict = {
                "implementation": server,
                "interface": self._testbed_server_interface if self._testbed else interface,
                "hostname": self._testbed_server if self._testbed else 'local',
                "log_dir": server_log_dir.name,
                "www_dir": testcase.www_dir(),
                "certs_dir": testcase.certs_dir(),
                "role": "server",
            }
            client_variables: dict = {
                "implementation": client,
                "interface": self._testbed_client_interface if self._testbed else interface,
                "hostname": self._testbed_client if self._testbed else 'local',
                "log_dir": client_log_dir.name,
                "sim_log_dir": sim_log_dir.name,
                "download_dir": testcase.download_dir(),
                "role": "client",
            }

            server_variables = {**self._server_implementation_params, **server_variables}
            client_variables = {**self._client_implementation_params, **client_variables}

            if self._testbed:
                self._testbed_management._set_variables_on_machine(
                    self._testbed_server,
                    server_variables
                )
                self._testbed_management._set_variables_on_machine(
                    self._testbed_client,
                    client_variables
                )

                # Execute List of Server Pre Run Scripts if given
                if len(self._server_pre_scripts) > 0:
                    for server_script in self._server_pre_scripts:
                        self._testbed_management._run_script_on_machine(
                            host = self._testbed_server,
                            script_path = server_script
                        )

                # Execute List of Client Pre Run Scripts if given
                if len(self._client_pre_scripts) > 0:
                    for client_script in self._client_pre_scripts:
                        self._testbed_management._run_script_on_machine(
                            host = self._testbed_client,
                            script_path = client_script
                        )

            # Run Server
            self.logger.debug(f'Starting server:\n {server_cmd}\n')
            if self._testbed:
                s = subprocess.Popen(
                    server_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                s = subprocess.Popen(
                    server_cmd,
                    shell=True,
                    cwd=os.path.join(self._implementations_directory, self._implementations[server]['path']),
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            time.sleep(2)

            # Run Client
            self.logger.debug(f'Starting client:\n {client_cmd}\n')
            if self._testbed:
                testcase._start_time = datetime.now()
                c = subprocess.Popen(
                    client_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                testcase._start_time = datetime.now()
                c = subprocess.Popen(
                    client_cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    cwd=os.path.join(self._implementations_directory, self._implementations[client]['path'])
                )
            c_stdout, c_stderr = c.communicate(timeout=testcase.timeout())
            testcase._end_time = datetime.now()
            output = (c_stdout.decode("utf-8") if c_stdout else '') + \
                     (c_stderr.decode("utf-8") if c_stderr else '')

        except subprocess.TimeoutExpired as ex:
            self.logger.error(colored(f"Client expired: {ex}", 'red'))
            expired = True
        finally:
            # Remove bandwidth limit if was set
            if self._testbed and testcase.is_bandwidth_limited():
                self._remove_server_bandwidth_limit()

            # Execute List of Server Post Run Scripts given
            if self._testbed:
                if len(self._server_post_scripts) != 0:
                    for server_script in self._server_post_scripts:
                        self._testbed_management._run_script_on_machine(
                            host = self._testbed_server,
                            script_path = server_script
                        )
                
                # Execute List of Client Post Run Scripts if given
                if len(self._client_post_scripts) != 0:
                    for client_script in self._client_post_scripts:
                        self._testbed_management._run_script_on_machine(
                            host = self._testbed_client,
                            script_path = client_script
                        )
            
            # Remove delay if was set
            if self._testbed and testcase.is_client_delay_added():
                self._remove_client_delay()
            if self._testbed and testcase.is_server_delay_added():
                self._remove_server_delay()

            time.sleep(1)
            if self._testbed:
                if testcase.use_tcpdump():
                    subprocess.Popen(f'ssh {self._testbed_client} pkill -f tcpdump', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if testcase.use_ifstat():
                    subprocess.Popen(f'ssh {self._testbed_client} pkill -f ifstat', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                subprocess.Popen(f'ssh {self._testbed_server} pkill -f server', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            else:
                if testcase.use_tcpdump():
                    kill(trace.pid)
                if testcase.use_ifstat():
                    kill(ifstat.pid)
                kill(s.pid)

            # Unset client and server variables
            #
            # This step is necessary as otherwise set variables will stay
            # for future testcases/measurements if not set to another value
            if self._testbed:
                self._testbed_management._remove_all_variables_from_machine(
                    self._testbed_server
                )
                self._testbed_management._remove_all_variables_from_machine(                    
                    self._testbed_client
                )

            if not expired:
                log_process(c_stdout, c_stderr, 'Client')

            if testcase.use_tcpdump():
                log_process(*trace.communicate(), 'tcpdump')
            if testcase.use_ifstat():
                log_process(*ifstat.communicate(), 'ifstat')
            s_output = s.communicate()
            log_process(*s_output, 'Server')

            # TODO:
            #   instead of pulling the download dir from the client,
            #   calculate the hash there already
            if self._testbed:
                for dir in [server_log_dir.name, testcase.certs_dir()]:
                    self._pull_directory_from_remote(self._testbed_server, dir)
                for dir in [sim_log_dir.name, client_log_dir.name]:
                    self._pull_directory_from_remote(self._testbed_client, dir)

        # Try to compute transmission time from client logs
        if self._use_client_timestamps:
            try:
                with open(os.path.join(client_log_dir.name, 'time.json')) as f:
                    data = json.load(f)

                    new_start = datetime.fromtimestamp(data['start'] / 10**9)
                    new_end = datetime.fromtimestamp(data['end'] / 10**9)

                    old_duration = testcase._end_time - testcase._start_time
                    new_duration = new_end - new_start

                    self.logger.debug(f'Interop duration: {old_duration}')
                    self.logger.debug(f'Client  duration: {new_duration}')
                    self.logger.debug('Difference: {:.2f}%'.format((old_duration - new_duration) / old_duration * 100))

                    testcase._start_time = new_start
                    testcase._end_time = new_end

            except Exception as e:
                self.logger.error(f'Failed to read time.json: {e}')

        # Todo End
        if s.returncode == 127 \
                or self._is_unsupported(s_output[0].decode("utf-8").splitlines()) \
                or self._is_unsupported(s_output[1].decode("utf-8").splitlines()):
            self.logger.error(colored(f"server does not support the test", 'red'))
            self._set_testcase_unsupported(name=server, role='server', testcase=testcase.name())
            status = TestResult.UNSUPPORTED
        elif not expired:
            lines = output.splitlines()
            if c.returncode == 127 or self._is_unsupported(lines):
                self.logger.error(colored(f"client does not support the test", 'red'))
                self._set_testcase_unsupported(name=client, role='client', testcase=testcase.name())
                status = TestResult.UNSUPPORTED
            elif c.returncode == 0 or any("client exited with code 0" in str(line) for line in lines):
                try:
                    status = testcase.check() if not self._testbed else testcase.check(self._testbed_client, self._testbed_server)
                except Exception as e:
                    self.logger.error(colored(f"testcase.check() threw Exception: {e}", 'red'))
                    status = TestResult.FAILED
            else:
                self.logger.error(colored(f"Client or server failed", 'red'))
                status = TestResult.FAILED
        else:
            self.logger.error(colored(f"Client or server expired", 'red'))
            status = TestResult.FAILED

        if status == TestResult.SUCCEEDED:
            self.logger.info(colored(f"\u2713 Test successful", 'green'))
        elif status == TestResult.FAILED:
            self.logger.info(colored(f"\u2620 Test failed", 'red'))
        elif status == TestResult.UNSUPPORTED:
            self.logger.info(colored(f"? Test unsupported", 'yellow'))

        # save logs
        self.logger.removeHandler(log_handler)
        log_handler.close()
        if status == TestResult.FAILED or status == TestResult.SUCCEEDED:
            log_dir = self._log_dir + "/" + server + "_" + client + "/" + str(testcase)
            if log_dir_prefix:
                log_dir += "/" + log_dir_prefix
            shutil.copytree(server_log_dir.name, log_dir + "/server")
            shutil.copytree(client_log_dir.name, log_dir + "/client")
            shutil.copytree(sim_log_dir.name, log_dir + "/sim")
            shutil.copyfile(log_file.name, log_dir + "/output.txt")
            if self._save_files and status == TestResult.FAILED:
                shutil.copytree(testcase.www_dir(), log_dir + "/www")
                try:
                    shutil.copytree(testcase.download_dir(), log_dir + "/downloads")
                except Exception as exception:
                    self.logger.info("Could not copy downloaded files: %s", exception)

        if self._testbed:
            self._delete_remote_directory(self._testbed_server, server_log_dir.name)
            self._delete_remote_directory(self._testbed_server, testcase.www_dir())
            self._delete_remote_directory(self._testbed_server, testcase.certs_dir())
            self._delete_remote_directory(self._testbed_client, client_log_dir.name)
            self._delete_remote_directory(self._testbed_client, sim_log_dir.name)
            self._delete_remote_directory(self._testbed_client, testcase.download_dir())

        testcase.cleanup()
        server_log_dir.cleanup()
        client_log_dir.cleanup()
        self.logger.debug("Test took %ss", (datetime.now() - start_time).total_seconds())

        # measurements also have a value
        if hasattr(testcase, "result"):
            value = testcase.result()
        else:
            value = None

        return status, value

    def _run_measurement(
        self, server: str, client: str, test: Callable[[], testcases.Measurement]
    ) -> MeasurementResult:
        values = []
        for i in range(0, test.repetitions()):
            self.logger.info(f"Run measurement {i + 1}/{test.repetitions()}")
            result, value = self._run_test(server, client, "%d" % (i + 1), test)
            if result != TestResult.SUCCEEDED:
                if self._continue_on_error:
                    continue
                res = MeasurementResult()
                res.result = result
                res.details = ""
                return res
            values.append(value)

        self.logger.debug(values)
        res = MeasurementResult()
        res.result = TestResult.SUCCEEDED
        res.all_infos = values
        res.details = ""

        if len(values) > 0:
            mean = statistics.mean(values)
            stdev = statistics.stdev(values) if len(values) > 1 else 0

            res.details = "{:.2f} (± {:.2f}) {}".format(
                mean, stdev, test.unit()
            )
        else:
            res.result = TestResult.FAILED
        return res

    def _setup_env(self, path, name, role):
        """Creates a python venv for this role and
        executes the implementations setup-env.sh script in this python
        venv; both tasks either locally or remotely using ssh in testbed mode.
        """
        try:
            if name in self._prepared_envs[role]:
                return

            venv_command = self._get_venv(name, role)
            cmd = venv_command + "; ./setup-env.sh"

            if self._testbed:
                cmd = f'ssh {self._testbed_server if role == "server" else self._testbed_client} "cd {path}; {cmd}"'

            self.logger.debug(f'Setup:\n {cmd}\n')

            if self._testbed:
                setup_env = subprocess.Popen(
                    cmd,
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )
            else:
                setup_env = subprocess.Popen(
                    cmd,
                    cwd=os.path.join(self._implementations_directory, self._implementations[name]['path']),
                    shell=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

            log_process(*setup_env.communicate(timeout=120), 'setup_env')
            self._prepared_envs[role].append(name)
        except subprocess.TimeoutExpired as ex:
            self.logger.error(colored(f"Setup environment timeout for {name} ({role})", 'red'))
            return ex
        return

    def _get_max_filesize(self, client: str, server: str):
        """Check if there is a file size limitation for the given client server implementation"""

        sizes = list(filter(None, [
            self._implementations[client].get('max_filesize', None),
            self._implementations[server].get('max_filesize', None)
        ]))
        return min(sizes, default=None)

    def run(self):
        """run the interop test suite and output the table"""

        if self._testbed:
            self.logger.info(colored(f'Testbed mode: {self._testbed_server}-{self._testbed_client}', 'white', attrs=['bold']))
        
        nr_failed = 0
        self.logger.info(colored(f"Saving logs to {self._log_dir}", "yellow", attrs=['bold']))
        self.logger.info(colored(f'Servers: {" ".join(self._servers)}', 'yellow', attrs=['bold']))
        self.logger.info(colored(f'Clients: {" ".join(self._clients)}', 'yellow', attrs=['bold']))
        if len(self._tests) > 0:
            self.logger.info(colored(f'Testcases: {" ".join(map(lambda x: x.name(), self._tests))}', 'yellow', attrs=['bold']))
        if len(self._measurements) > 0:
            self.logger.info(colored(f'Measurements: {" ".join(map(lambda x: x.name(), self._measurements))}', 'yellow', attrs=['bold']))

        total_tests = len(self._servers) * len(self._clients) * (len(self._tests) + len(self._measurements))
        finished_tests = 0

        # Copy implementations to remote hosts
        self._copy_implementations()

        for server in self._servers:
            path = self._implementations[server]["path"]
            if self._setup_env(path, name=server, role="server") is not None:
                continue

            if not self._check_impl_is_compliant(server, role='server'):
                self.logger.info(colored(f"Server {server} is not compliant, skipping", "red"))
                finished_tests += (len(self._tests) + len(self._measurements)) * len(self._clients)
                continue

            for client in self._clients:

                if self._only_same_implementation or self._is_client_or_server_solomode(client, server):
                    if client != server:
                        finished_tests += len(self._tests) + len(self._measurements)
                        continue

                path = self._implementations[client]["path"]
                if self._setup_env(path, name=client, role="client") is not None:
                    continue

                if not self._check_impl_is_compliant(client, role='client'):
                    self.logger.info(colored(f"Client {client} is not compliant, skipping", "red"))
                    finished_tests += len(self._tests) + len(self._measurements)
                    continue

                self.logger.debug(
                    "Running with server %s (%s) and client %s (%s)",
                    server,
                    self._implementations[server]["path"],
                    client,
                    self._implementations[client]["path"],
                )

                # run the test cases
                for testcase in self._tests:
                    finished_tests += 1

                    self.logger.info(
                        colored(
                            "\n---\n"
                            + f"{finished_tests}/{total_tests}\n"
                            + f"Test: {testcase.name()}\n"
                            + f"Server: {server}  "
                            + f"Client: {client}\n"
                            + "---",
                            'cyan',
                            attrs=['bold']
                        )
                    )

                    status = self._run_testcase(server, client, testcase)
                    self.test_results[server][client][testcase] = status
                    if status == TestResult.FAILED:
                        nr_failed += 1

                # run the measurements
                for measurement in self._measurements:
                    finished_tests += 1

                    self.logger.info(
                        colored(
                            "\n---\n"
                            + f"{finished_tests}/{total_tests}\n"
                            + f"Measurement: {measurement.name()}\n"
                            + f"Server: {server}\n"
                            + f"Client: {client}\n"
                            + "---",
                            'magenta',
                            attrs=['bold']
                        )
                    )

                    res = self._run_measurement(server, client, measurement)
                    self.measurement_results[server][client][measurement] = res

        self._print_results()
        self._export_results()
        return nr_failed
