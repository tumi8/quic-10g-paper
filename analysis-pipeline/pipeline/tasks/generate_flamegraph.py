import os
import subprocess

from .abstract_task import Task

class GenerateFlamegraph(Task):

    @staticmethod
    def desc():
        return "Generate Flamegraph with FlameGraph tool for perf..."

    def run(self):
        dir = self._params["dir"]
        FLAMEGRAPH_DIR = self._params["FLAMEGRAPH_DIR"]
        desc = "generating flame graph"

        cmd_suffix = " ".join([os.path.join(dir, "out.annotated.folded"), ">", os.path.join(dir, "out.svg")])
        
        cmd = " ".join(
            [
                os.path.join(FLAMEGRAPH_DIR, "flamegraph.pl"),
                "--subtitle",
                dir,
                "--width 1500",
                "--minwidth 1",
                "--colors java",
                cmd_suffix
            ]
        )

        p2 = subprocess.Popen(
            cmd,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p2.communicate()
        return (p2.returncode == 0, desc)

