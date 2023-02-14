#!/usr/bin/python3

import os
import re
import json
import logging
import argparse

import numpy as np
import pandas

from util.trace import Direction, PacketType, TraceAnalyzer


from ast import literal_eval  # convert str to dict
from abc import ABC, abstractmethod


class Parser(ABC):
    """A Parser can extract a result from a interop runner logdir,
    given a logdir, an implementation pair, a testcase and a repetition.
    See the example below to see how a goodput result for a certain result is
    extracted.
    """

    @abstractmethod
    def columnheader(self) -> str:
        """The columnheader is the string that is the title for a column of
        a pandas dataframe.
        """
        pass

    def column_amount(self) -> str:
        """This method should return the amount of columns that this parser
        will return. If this method returns 1, the data returned by the
        parse an columnheader methods will be a single value. If this method
        returns more than 1, the data returned by the parse and columnheader
        methods will be a list of values.
        """
        if type(self.columnheader()) is list:
            return len(self.columnheader())
        elif type(self.columnheader()) is str:
            return 1
        else:
            raise Exception("Unknown column header")

    @abstractmethod
    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        """A check whether this parser should be run by checking if any
        requirements are fulfilled, e.g., files exist in locations
        Runs the parse function on True.
        """
        pass

    @abstractmethod
    def parse(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ):
        """This method does the heavy lifting of extracting the information
        that this parser should extract. It is called for each repetition
        inside the logdir, so it should return repetition specific information,
        e.g., the goodput result of each repetition.
        """
        pass


class GoodputParser(Parser):
    def columnheader(self) -> [str]:
        return ["goodput", "filesize"]

    @staticmethod
    def _result_file(logdir):
        return os.fsdecode(
            os.path.join(
                os.fsencode(logdir),
                os.fsencode("result.json"),
            )
        )

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        return os.path.exists(self._result_file(logdir))

    def parse(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ):
        results_file_path = self._result_file(logdir)
        with open(results_file_path) as f:
            data_dict = json.load(f)
            server, client = split_implementation_pair(implementation_pair)

            measurements = [
                res for results in data_dict["measurements"] for res in results
            ]

            sample = [
                res
                for res in measurements
                if res["server"] == server and res["client"] == client
            ]

            if len(sample) != 1:
                logging.debug(f"└─ Skipping, found {len(sample)} results")
                return None, None

            details = sample[0]["details"]
            filesize = sample[0]["filesize"]
            if len(details) < repetition:
                logging.debug(f"└─ Skipping, found {len(details)} repetitions")
                return None, None

            # Returns result of repetition (starting with 1)
            return details[repetition - 1], filesize


class ServerThroughputOutgoingParser(Parser):
    _ifstat_filename = "ifstat.log"

    def columnheader(self) -> str:
        return "server_throughput_outgoing"

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        ifstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode("server"),
            os.fsencode(self._ifstat_filename),
        )
        return os.path.exists(ifstat_path)

    def parse(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ):
        ifstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode("server"),
            os.fsencode(self._ifstat_filename),
        )
        try:
            with open(os.fsdecode(ifstat_path)) as f:
                lines = f.readlines()
        except FileNotFoundError:
            return []
        # Remove leading and trailing spaces of each line
        lines = [line.rstrip() for line in lines]
        lines = [line.lstrip() for line in lines]
        # Remove heading
        lines.pop(0)
        lines.pop(0)
        lines.pop(0)
        # Only second element which is outgoing bits per second
        lines = [line.split() for line in lines]
        lines = [line[1] for line in lines]
        # To Numbers
        lines = [literal_eval(line) for line in lines]
        # Remove zeroes
        lines = [line for line in lines if line != 0.0]
        # Remove first and last 8 elements
        for i in range(0, 8):
            lines.pop(0)
            lines.pop()
        # Change Kbps to Mbps
        lines = [line / 1000 for line in lines]
        return lines


class ServerThroughputIncomingParser(Parser):
    _ifstat_filename = "ifstat.log"

    def columnheader(self) -> str:
        return "server_throughput_incoming"

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        ifstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode("server"),
            os.fsencode(self._ifstat_filename),
        )
        return os.path.exists(ifstat_path)

    def parse(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ):
        ifstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode("server"),
            os.fsencode(self._ifstat_filename),
        )
        try:
            with open(os.fsdecode(ifstat_path)) as f:
                lines = f.readlines()
        except FileNotFoundError:
            return []
        # Remove leading and trailing spaces of each line
        lines = [line.rstrip() for line in lines]
        lines = [line.lstrip() for line in lines]
        # Remove heading
        lines.pop(0)
        lines.pop(0)
        lines.pop(0)
        # Only second element which is outgoing bits per second
        lines = [line.split() for line in lines]
        lines = [line[0] for line in lines]
        # To Numbers
        lines = [literal_eval(line) for line in lines]
        # Remove zeroes
        lines = [line for line in lines if line != 0.0]
        # Remove first and last 8 elements
        for i in range(0, 8):
            lines.pop(0)
            lines.pop()
        # Change Kbps to Mbps
        lines = [line / 1000 for line in lines]
        return lines


class ClientThroughputOutgoingParser(Parser):
    _ifstat_filename = "ifstat.log"

    def columnheader(self) -> str:
        return "client_throughput_outgoing"

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        ifstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode("client"),
            os.fsencode(self._ifstat_filename),
        )
        return os.path.exists(ifstat_path)

    def parse(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ):
        ifstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode("client"),
            os.fsencode(self._ifstat_filename),
        )
        try:
            with open(os.fsdecode(ifstat_path)) as f:
                lines = f.readlines()
        except FileNotFoundError:
            return []
        # Remove leading and trailing spaces of each line
        lines = [line.rstrip() for line in lines]
        lines = [line.lstrip() for line in lines]
        # Remove heading
        lines.pop(0)
        lines.pop(0)
        lines.pop(0)
        # Only second element which is outgoing bits per second
        lines = [line.split() for line in lines]
        lines = [line[1] for line in lines]
        # To Numbers
        lines = [literal_eval(line) for line in lines]
        # Remove zeroes
        lines = [line for line in lines if line != 0.0]
        # Remove first and last 8 elements
        for i in range(0, 8):
            lines.pop(0)
            lines.pop()
        # Change Kbps to Mbps
        lines = [line / 1000 for line in lines]
        return lines


class ClientThroughputIncomingParser(Parser):
    _ifstat_filename = "ifstat.log"

    def columnheader(self) -> str:
        return "client_throughput_incoming"

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        ifstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode("client"),
            os.fsencode(self._ifstat_filename),
        )
        return os.path.exists(ifstat_path)

    def parse(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ):
        ifstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode("client"),
            os.fsencode(self._ifstat_filename),
        )
        try:
            with open(os.fsdecode(ifstat_path)) as f:
                lines = f.readlines()
        except FileNotFoundError:
            return []
        # Remove leading and trailing spaces of each line
        lines = [line.rstrip() for line in lines]
        lines = [line.lstrip() for line in lines]
        # Remove heading
        lines.pop(0)
        lines.pop(0)
        lines.pop(0)
        # Only second element which is outgoing bits per second
        lines = [line.split() for line in lines]
        lines = [line[0] for line in lines]
        # To Numbers
        lines = [literal_eval(line) for line in lines]
        # Remove zeroes
        lines = [line for line in lines if line != 0.0]
        # Remove first and last 8 elements
        for i in range(0, 8):
            lines.pop(0)
            lines.pop()
        # Change Kbps to Mbps
        lines = [line / 1000 for line in lines]
        return lines


class CpuUtilParser(Parser):
    _pidstat_filename = "pidstat.txt"
    _append_avg_column = True
    _role = "client"

    def columnheader(self) -> str:
        return (
            self._role + "_cpu"
            if not self._append_avg_column
            else [self._role + "_cpu", self._role + "_cpu_avg"]
        )

    def column_amount(self) -> str:
        return 1 if not self._append_avg_column else 2

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        pidstat_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode(self._role),
            os.fsencode(self._pidstat_filename),
        )
        return os.path.exists(pidstat_path)

    def parse(
        self,
        logdir: str,
        implementation_pair: str = "quiche_quiche",
        testcase: str = "goodput",
        repetition: int = 1,
    ) -> dict:
        """Parsing function for cpu utilization of client and server of a
        interop framework logfile.

        Keyword arguments:
        logdir     -- the path to the logdir to extract cpu util values from
        implementation_pair -- the implementation pair you are interested in
        testcase   -- the testcase you are interested in
        repetition -- the one repetition to get the cpu util info from

        Returns:
        A list of cpu utilization floats
        None on error
        """
        repetition_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
        )
        if not os.path.exists(repetition_path):
            return None

        server, client = implementation_pair.split("_")

        if self._role == "client":
            implementation = client
        elif self._role == "server":
            implementation = server

        linematch_string = None
        if implementation.startswith("quiche"):
            linematch_string = "quiche"
        elif implementation.startswith("lsquic"):
            linematch_string = "http_" + self._role
        elif implementation.startswith("mvfst"):
            linematch_string = "hq"
        elif implementation.startswith("picoquic"):
            linematch_string = "picoquicdemo"
        elif implementation in ["tcp+tls", "tcp", "tls1.3"]:
            if self._role == "client":
                linematch_string = "wget"
            elif self._role == "server":
                linematch_string = "nginx-server"

        if linematch_string == "":
            raise NotImplementedError(
                "The function parse_pidstat_cpuutil() did not recognize the "
                f"implementation pair it was given: {implementation_pair} "
                "Please implement the correct "
                "line match string so that the pidstat file can be filtered "
                "correctly to only yield wanted cpu util results! "
                "Alternatively make sure to remove the logfile that had the "
                f"unknown implementation: {logdir}"
            )

        pidstat_path = os.fsdecode(
            os.path.join(
                repetition_path,
                os.fsencode(self._role),
                os.fsencode(self._pidstat_filename),
            )
        )

        cpuutil: [float] = get_cpu_util_from_pidstat_file(
            pidstat_log_path=pidstat_path, line_match_string=linematch_string
        )
        return (
            cpuutil if not self._append_avg_column else [cpuutil, np.average(cpuutil)]
        )


class ClientCpuUtilParser(CpuUtilParser):
    _role = "client"


class ServerCpuUtilParser(CpuUtilParser):
    _role = "server"


class EthtoolStatsParser(Parser):
    _filename_start = "ethtool-start.txt"
    _filename_stop = "ethtool-stop.txt"
    _role = "client"

    def columnheader(self):
        return [
            # self._role + "_ethtool_stats",
            self._role + "_ethtool_rx_total_discard_pkts",
            self._role + "_ethtool_tx_total_discard_pkts",
            self._role + "_ethtool_rx_bytes",
            self._role + "_ethtool_tx_bytes",
            self._role + "_ethtool_rx_total_frames",
            self._role + "_ethtool_tx_total_frames",
        ]

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        file_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode(self._role),
            os.fsencode(self._filename_stop),
        )
        return os.path.exists(file_path)

    def parse(
        self,
        logdir: str,
        implementation_pair: str = "quiche_quiche",
        testcase: str = "goodput",
        repetition: int = 1,
    ) -> dict:
        """Parsing function for ethtool -S output of client and server of a
        interop framework logfile.

        Keyword arguments:
        logdir     -- the path to the logdir to extract perf values from
        implementation_pair -- the implementation pair you are interested in
        testcase   -- the testcase you are interested in
        repetition -- the one repetition to get the cpu util info from

        Returns:
        A XY #TODO
        None on error
        """
        repetition_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
        )
        if not os.path.exists(repetition_path):
            return [None for _ in self.column_amount()]
        else:
            # parse ethtool files
            start_file_path = os.path.join(
                repetition_path,
                os.fsencode(self._role),
                os.fsencode(self._filename_start),
            )
            stop_file_path = os.path.join(
                repetition_path,
                os.fsencode(self._role),
                os.fsencode(self._filename_stop),
            )
            result = {}
            with open(stop_file_path) as f:
                lines = f.readlines()
                for l in lines:
                    try:
                        k, v = l.split(": ")
                        result[k.strip()] = int(v)
                    except ValueError:
                        pass
            with open(start_file_path) as f:
                lines = f.readlines()
                for l in lines:
                    try:
                        k, v = l.split(": ")
                        result[k.strip()] -= int(
                            v
                        )  # Subtract start values from end values
                    except ValueError:
                        pass

            return [
                # result,
                result.get("rx_total_discard_pkts", None),
                result.get("tx_total_discard_pkts", None),
                result.get("rx_bytes", None),
                result.get("tx_bytes", None),
                result.get("rx_total_frames", None),
                result.get("tx_total_frames", None),
            ]


class ClientEthtoolStatsParser(EthtoolStatsParser):
    _role = "client"


class ServerEthtoolStatsParser(EthtoolStatsParser):
    _role = "server"


class TcStatsParser(Parser):
    _filename = "tc-stats.txt"
    _role = "client"

    def columnheader(self) -> str:
        return self._role + "_tc_stats"

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        file_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode(self._role),
            os.fsencode(self._filename),
        )
        return os.path.exists(file_path)

    def parse(
        self,
        logdir: str,
        implementation_pair: str = "quiche_quiche",
        testcase: str = "goodput",
        repetition: int = 1,
    ) -> dict:
        """Parsing function for tc -s -d ... output of client and server of a
        interop framework logfile.

        Keyword arguments:
        logdir     -- the path to the logdir to extract perf values from
        implementation_pair -- the implementation pair you are interested in
        testcase   -- the testcase you are interested in
        repetition -- the one repetition to get the cpu util info from

        Returns:
        A XY #TODO
        None on error
        """
        repetition_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
        )
        if not os.path.exists(repetition_path):
            return None
        else:
            # parse tc-stats files
            file_path = os.path.join(
                repetition_path, os.fsencode(self._role), os.fsencode(self._filename)
            )

            with open(file_path) as f:
                data = f.read()

                regex = r"^qdisc netem.*root.*limit (\d+) delay (\d+ms)\s.*bytes (\d+) pkt \(dropped (\d+),.*$"
                matches = re.findall(regex, data, re.MULTILINE)

                if len(matches) == 0:
                    return {}
                else:
                    return {
                        "delay": matches[0][1],
                        "limit": int(matches[0][0]),
                        "packets": int(matches[0][2]),
                        "dropped": int(matches[0][3]),
                    }


class ClientTcStatsParser(TcStatsParser):
    _role = "client"


class ServerTcStatsParser(TcStatsParser):
    _role = "server"


class NetstatStatsParser(Parser):
    _filename_start = "netstat-start.txt"
    _filename_stop = "netstat-stop.txt"
    _role = "client"

    def columnheader(self):
        return [
            # self._role + "_netstat_stats",
            self._role + "_netstat_packets_received",
            self._role + "_netstat_packets_to_unknown_port_received",
            self._role + "_netstat_packet_receive_errors",
            self._role + "_netstat_packets_sent",
            self._role + "_netstat_receive_buffer_errors",
            self._role + "_netstat_send_buffer_errors",
        ]

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        file_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode(self._role),
            os.fsencode(self._filename_stop),
        )
        return os.path.exists(file_path)

    def parse(
        self,
        logdir: str,
        implementation_pair: str = "quiche_quiche",
        testcase: str = "goodput",
        repetition: int = 1,
    ) -> dict:
        """Parsing function for netstat -su output of client and server of a
        interop framework logfile.

        Keyword arguments:
        logdir     -- the path to the logdir to extract perf values from
        implementation_pair -- the implementation pair you are interested in
        testcase   -- the testcase you are interested in
        repetition -- the one repetition to get the cpu util info from

        Returns:
        A XY #TODO
        None on error
        """
        repetition_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
        )
        if not os.path.exists(repetition_path):
            return [None * self.column_amount()]
        else:
            # parse netstat files
            start_file_path = os.path.join(
                repetition_path,
                os.fsencode(self._role),
                os.fsencode(self._filename_start),
            )
            stop_file_path = os.path.join(
                repetition_path,
                os.fsencode(self._role),
                os.fsencode(self._filename_stop),
            )
            result = {}

            with open(stop_file_path) as f:
                lines = f.readlines()
                udp_section_started = False
                udp_section_ended = False
                for l in lines:
                    if udp_section_started and not udp_section_ended:
                        try:
                            if not l.startswith(" "):
                                udp_section_ended = True
                                continue
                            v, k = l.strip().split(" ", 1)
                            result[k] = int(v)
                        except ValueError:
                            pass
                    if l.startswith("Udp:"):
                        udp_section_started = True
                        continue
            with open(start_file_path) as f:
                lines = f.readlines()
                udp_section_started = False
                udp_section_ended = False
                for l in lines:
                    if udp_section_started and not udp_section_ended:
                        try:
                            if not l.startswith(" "):
                                udp_section_ended = True
                                continue
                            v, k = l.strip().split(" ", 1)
                            if int(v):
                                result[k] -= int(v)
                        except ValueError:
                            pass
                    if l.startswith("Udp:"):
                        udp_section_started = True
                        continue

            return list(result.values())


class ClientNetstatStatsParser(NetstatStatsParser):
    _role = "client"


class ServerNetstatStatsParser(NetstatStatsParser):
    _role = "server"


class PerfParser(Parser):
    _perf_filename = "out.folded"
    _role = "client"

    def columnheader(self) -> str:
        return self._role + "_perf"

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        perf_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode(self._role),
            os.fsencode(self._perf_filename),
        )
        return os.path.exists(perf_path)

    def parse(
        self,
        logdir: str,
        implementation_pair: str = "quiche_quiche",
        testcase: str = "goodput",
        repetition: int = 1,
    ) -> dict:
        """Parsing function for perf output of client and server of a
        interop framework logfile.

        Keyword arguments:
        logdir     -- the path to the logdir to extract perf values from
        implementation_pair -- the implementation pair you are interested in
        testcase   -- the testcase you are interested in
        repetition -- the one repetition to get the cpu util info from

        Returns:
        A XY #TODO
        None on error
        """
        repetition_path = os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
        )
        if not os.path.exists(repetition_path):
            return None

        server, client = implementation_pair.split("_")

        if self._role == "client":
            implementation = client
        elif self._role == "server":
            implementation = server

        prefix = None
        if implementation.startswith("quiche"):
            prefix = f"quiche-{self._role};"
        elif implementation.startswith("lsquic"):
            prefix = f"http_{self._role};"

        if prefix == "":
            raise NotImplementedError(
                "The perf parser did not recognize the "
                f"implementation pair it was given: {implementation_pair} "
                "Please implement the correct prefix so that the perf "
                "output can be filtered correctly. Alternatively make sure "
                "to remove the logfile that had the unknown "
                f"implementation: {logdir}"
            )

        # prepare regex for checking lines in out.folded for validity
        regex_folded_stack_line = re.compile(r"(.*)\s(\d+)")

        # load mapping
        mapping = []
        with open(
            os.path.join("util", "perf", "mappings", implementation + ".json"),
            "r",
        ) as openfile:
            mapping = json.load(openfile)

        # helper function
        def add_to_dict_by_key_or_init(dict, key, add):
            if not dict.get(key):
                dict[key] = add
            else:
                dict[key] += add

        # parse perf file
        folded_file_path = os.path.join(
            repetition_path, os.fsencode(self._role), os.fsencode("out.folded")
        )
        with open(folded_file_path) as f:
            sum_samples = 0
            sum_samples_with_prefix = 0
            distribution = {}
            general_distribution = {}
            lines = f.readlines()
            for l in lines:
                m = regex_folded_stack_line.match(l)
                if m:
                    call, samples = m[1], int(m[2])
                    sum_samples += samples
                    if l.startswith(prefix):
                        sum_samples_with_prefix += samples
                        for mpng, mpng_cat in mapping.items():
                            if (
                                mpng.startswith("regex:")
                                and re.match(mpng[6:], call, re.IGNORECASE)
                            ) or call == mpng:
                                add_to_dict_by_key_or_init(
                                    distribution, mpng_cat, samples
                                )
                                gd_key = mpng_cat.split(" ")[0]
                                add_to_dict_by_key_or_init(
                                    general_distribution, gd_key, samples
                                )
                                break
                else:
                    raise ValueError(f"invalid line found in {folded_file_path}")

            return json.dumps(
                {
                    "SUM_SAMPLES": sum_samples,
                    "SUM_SAMPLES_QUIC": sum_samples_with_prefix,
                    "OVERVIEW": general_distribution,
                    "DETAILED": distribution,
                }
            )


class ClientPerfParser(PerfParser):
    _role = "client"


class ServerPerfParser(PerfParser):
    _role = "server"


class ClientRuntime(Parser):
    _filename = "time.json"
    _role = "client"

    def columnheader(self) -> str:
        return self._role + "_runtime"

    def _time_file(
        self,
        logdir: str,
        implementation_pair: str,
        testcase: str,
        repetition: int,
    ):
        return os.path.join(
            os.fsencode(logdir),
            os.fsencode(implementation_pair),
            os.fsencode(testcase),
            os.fsencode(str(repetition)),
            os.fsencode(self._role),
            os.fsencode(self._filename),
        )

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        return os.path.exists(
            self._time_file(logdir, implementation_pair, testcase, repetition)
        )

    def parse(
        self,
        logdir: str,
        implementation_pair: str = "quiche_quiche",
        testcase: str = "goodput",
        repetition: int = 1,
    ) -> dict:
        """Parsing the ime.json file to get the exact measurement duration."""

        path = self._time_file(logdir, implementation_pair, testcase, repetition)
        try:
            with open(path) as f:
                data = json.load(f)
                return (data["end"] - data["start"]) / 10**9  # Values are in ns
        except Exception as e:
            logging.debug(f"Failed to load time.json: {path} ({e})")
            return None


class PcapParser(Parser):
    _role = "client"

    def columnheader(self):
        return [
            self._role + "_transport_parameter",
            self._role + "_frame_size",
            self._role + "_udp_size",
        ]

    def _pcap_file(self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1):
        return os.path.join(
            logdir,
            implementation_pair,
            testcase,
            str(repetition),
            'sim',
            'trace.pcap'
        )

    def _key_file(self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1, role: str = _role):
        return os.path.join(
            logdir,
            implementation_pair,
            testcase,
            str(repetition),
            role,
            'keys.log'
        )

    def is_log_compliant(
        self, logdir: str, implementation_pair: str, testcase: str, repetition: int = 1
    ) -> bool:
        pcap_file = self._pcap_file(logdir, implementation_pair, testcase, repetition)
        client_keys = self._key_file(logdir, implementation_pair, testcase, repetition, 'client')
        server_keys = self._key_file(logdir, implementation_pair, testcase, repetition, 'server')
        return os.path.exists(pcap_file) and (os.path.exists(client_keys) or os.path.exists(server_keys))

    def parse(
        self,
        logdir: str,
        implementation_pair: str = "quiche_quiche",
        testcase: str = "goodput",
        repetition: int = 1,
    ) -> dict:

        client_keys = self._key_file(logdir, implementation_pair, testcase, repetition, 'client')
        server_keys = self._key_file(logdir, implementation_pair, testcase, repetition, 'server')
        key_file = client_keys if os.path.exists(client_keys) else server_keys
        pcap_file = self._pcap_file(logdir, implementation_pair, testcase, repetition)

        trace = TraceAnalyzer(
            pcap_file,
            key_file,
            ip4_server='10.0.0.2',
            port_server=4433,
        )

        trace = trace.get_raw_packets(Direction.FROM_CLIENT if self._role == 'client' else Direction.FROM_SERVER)

        eth_sizes = []
        udp_sizes = []
        quic_layers = []

        for packet in trace:
            eth_sizes.append(int(packet.length))
            for layer in packet:
                if layer.layer_name == 'udp':
                    udp_sizes.append(int(layer.length))
                elif layer.layer_name == 'quic':
                    quic_layers.append(layer)

        transport_parameter = []
        for layer in quic_layers:
            transport_fields = {k.replace('tls.quic.parameter.', ''): v for k, v in layer._all_fields.items() if k.startswith('tls.quic.parameter.')}
            if len(transport_fields) > 0:
                transport_parameter.append(transport_fields)
        return transport_parameter, eth_sizes, udp_sizes


class ClientPcapParser(PcapParser):
    _role = "client"


class ServerPcapParser(PcapParser):
    _role = "server"



def buildDataframe(
    rootdirs: [str],
):
    """Main function to start parsing a list of given root directories.
    Currently supports goodput and cpu util values of quiche and tcp+tls.

    Keyword arguments:
    rootdirs -- list of directories that contain interop logfiles in them
    """
    # Main data dict we transform to a dataframe later
    data = {}
    parsers = []
    parsers += [GoodputParser]
    parsers += [ServerCpuUtilParser]
    parsers += [ClientCpuUtilParser]
    parsers += [ServerThroughputOutgoingParser]
    parsers += [ServerThroughputIncomingParser]
    parsers += [ClientThroughputOutgoingParser]
    parsers += [ClientThroughputIncomingParser]
    parsers += [ClientPerfParser]
    parsers += [ServerPerfParser]
    parsers += [ClientEthtoolStatsParser]
    parsers += [ServerEthtoolStatsParser]
    parsers += [ClientNetstatStatsParser]
    parsers += [ServerNetstatStatsParser]
    parsers += [ClientTcStatsParser]
    parsers += [ServerTcStatsParser]
    parsers += [ClientRuntime]
    parsers += [ClientPcapParser]
    parsers += [ServerPcapParser]

    for rootdir in rootdirs:
        fs_rootdir = os.fsencode(rootdir)
        for fs_logdir in [x.name for x in os.scandir(fs_rootdir) if x.is_dir()]:
            # Assemble info from all parsers
            logdir_path = os.fsdecode(os.path.join(fs_rootdir, fs_logdir))
            parse_logdir(data, os.fsencode(logdir_path), *parsers)
    # Convert dict to pandas dataframe
    df = pandas.DataFrame(data)
    return df


def parse_logdir(data: dict, logdir: bytes, *parsers):
    """Return all dataframe lines as dicts that are contained in this dict,
    columns are determined by the given parsers.
    Should one parser fail for this logdir, all results are skipped and the
    user is notified with an exception.
    """
    logging.debug(f"Current logdir: {os.fsdecode(logdir)}")
    results_file_path = os.fsdecode(
        os.path.join(
            logdir,
            os.fsencode("result.json"),
        )
    )

    if not os.path.exists(results_file_path):
        logging.debug(f"└─ No results.json     skipping")
        return

    # Get logdir wide information: hostpair, bandwidth_limit
    hostpair = get_logdir_hostpair(results_file_path)
    bandwidth_limit = get_logdir_bandwidth(results_file_path)
    logging.debug(f"└─ hostpair: {hostpair}")
    logging.debug(f"└─ bandwidth_limit: {bandwidth_limit}")

    # Iterate over implementation pairs (e.g. quiche_quiche)
    for fs_implementation_pair in os.listdir(logdir):
        fs_path_implementation_pair = os.path.join(logdir, fs_implementation_pair)
        if not os.path.isdir(fs_path_implementation_pair):
            continue

        implementation_pair = os.fsdecode(fs_implementation_pair)
        logging.debug(f"└─ Current implementation pair: {implementation_pair}")

        server, client = split_implementation_pair(implementation_pair)
        # Could iterate over testcases here, currently we simply hardcode goodput
        testcase = "goodput"

        # Iterate over repetitions
        repetition_amount = get_logdir_repetition_amount(logdir, implementation_pair)
        for repetition in range(1, repetition_amount + 1):
            logging.debug(f"   └─ Current repetition: {repetition}")
            # Fill dataframe row
            if "logdir" not in data:
                data["logdir"] = []
            data["logdir"].append(os.fsdecode(logdir))
            if "hostpair" not in data:
                data["hostpair"] = []
            data["hostpair"].append(hostpair)
            if "server" not in data:
                data["server"] = []
            data["server"].append(server)
            if "client" not in data:
                data["client"] = []
            data["client"].append(client)
            if "bw_limit" not in data:
                data["bw_limit"] = []
            # if bw is None, set string 'none'
            if bandwidth_limit == None:
                data["bw_limit"].append("none")
            else:
                data["bw_limit"].append(bandwidth_limit)
            if "repetition" not in data:
                data["repetition"] = []
            data["repetition"].append(repetition)
            # Iterate over all given parser and append their columname and
            # information to the current row
            for parser in parsers:
                # Only execute this parser if the logfile fulfills all
                # requirements
                p = parser()
                if p.is_log_compliant(
                    logdir=os.fsdecode(logdir),
                    implementation_pair=implementation_pair,
                    testcase=testcase,
                    repetition=repetition,
                ):
                    out = p.parse(
                        logdir=os.fsdecode(logdir),
                        implementation_pair=implementation_pair,
                        testcase=testcase,
                        repetition=repetition,
                    )
                    if out is None:
                        pass
                        logging.debug(
                            f"Parser {parser.__name__} failed with logdir {logdir}, \n"
                            f"implementation pair {implementation_pair}, \n"
                            f"testcase {testcase} and repetition {repetition}.\n"
                        )
                    if p.column_amount() == 1:
                        if p.columnheader() not in data:
                            data[p.columnheader()] = []
                        data[p.columnheader()].append(out)
                    elif p.column_amount() > 1:
                        for i, ch in enumerate(p.columnheader()):
                            if ch not in data:
                                data[ch] = []
                            data[ch].append(out[i])

                    # logging.debug(f"      └─ Current parser: {p.__name__}, result: {out}")
                else:
                    logging.debug(f"      └─  Parser {parser.__name__} not compliant with {logdir}")
                    chs = p.columnheader() if p.column_amount() > 1 else [p.columnheader()]
                    for ch in chs:
                        if ch not in data:
                            data[ch] = []
                        data[ch].append(None)
    return


def create_key_if_nonexistent(dictionary: dict, key: str):
    # Note: python handles mutable datastructures as call by reference
    if key not in dictionary:
        dictionary[key] = []


def get_logdir_hostpair(results_file_path: str) -> (str, str):
    """Returns server-client tuple of server and client name, given
    a result.json file
    """
    with open(results_file_path) as f:
        data_dict = json.load(f)
        server_node = data_dict.get("server_node_name")
        client_node = data_dict.get("client_node_name")

        if not server_node or not client_node:
            return "local"

        return "-".join([server_node, client_node])


def split_implementation_pair(implementation_pair: str) -> (str, str):
    """Returns (server, client) tuple of server and client implementation
    names, given the sting "server_client"
    """
    # Log directories are formatted as server_client
    return implementation_pair.split("_")


def get_logdir_bandwidth(results_file_path: str) -> str:
    """Returns bandwidth limit of  given
    a result.json file
    No limit returns the string "None"
    """
    with open(results_file_path) as f:
        # convert string to dict: https://stackoverflow.com/a/988251
        data_dict = json.load(f)
        bandwidth_limit = data_dict.get("bandwidth_limit")
        if bandwidth_limit == "None":
            return None
        else:
            return bandwidth_limit


def get_logdir_repetition_amount(
    logdir: str, implementation_pair: str, testcase: str = "goodput"
) -> int:
    path = os.path.join(
        os.fsencode(logdir), os.fsencode(implementation_pair), os.fsencode(testcase)
    )
    return len([x for x in os.scandir(path) if x.is_dir()])


def get_cpu_util_from_pidstat_file(
    pidstat_log_path: str, line_match_string: str
) -> [float]:
    """Given a pidstat logfile, return the CPU utilization values as a list
    of floats.
    line_match_string: the string a line that every line with a CPU util
                       value has matches with. This is the name of the
                       program that pidstat was made to observe

    Return [] empty list should the file not exist
    """
    lines = []
    try:
        with open(pidstat_log_path) as f:
            lines = f.readlines()
            lines = [line.rstrip() for line in lines]
    except FileNotFoundError:
        return []
    # Get only lines with CPU util value
    lines = list(filter(lambda string: line_match_string in string, lines))

    # Remove average line
    try:
        lines.pop()
    except IndexError:
        return []

    # Remove first 2 and last 2 values
    lines.pop(0)
    lines.pop(0)
    lines.pop()
    lines.pop()

    # Remove everything but the CPU util number
    result = []
    for line in lines:
        result.append(float(line[61:67]))

    return result


def save_df(df, outfile):
    df.to_csv(outfile, index=False)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-r",
        "--rootdirs",
        nargs="+",
        required=True,
        help="A list of directories containing logdirs inside them",
    )
    parser.add_argument("-o", "--output", help="Where to output the csv file")
    parser.add_argument(
        "-d", "--debug", help="enable DEBUG output", action="store_true"
    )
    args = parser.parse_args()

    if args.debug:
        logging.basicConfig(format="%(message)s", level=logging.DEBUG)

    df = buildDataframe(args.rootdirs)

    if not args.output:
        args.output = os.path.join(args.rootdirs[0], "processed.csv")

    save_df(df, args.output)


if __name__ == "__main__":
    main()
