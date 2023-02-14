import os
import sys
import subprocess

from .abstract_task import Task

class FoldStacks(Task):

    @staticmethod
    def desc():
        return "Folding stacks with FlameGraph tool for perf..."

    def run(self):
        """
        Expects the following parameters in the params dict:
        dir: the directory containing out.perf
        """
        dir = self._params["dir"]
        infile = os.path.join(dir, "out.perf.trimmed")
        outfile = os.path.join(dir, "out.folded")
        outfile_annotated = os.path.join(dir, "out.annotated.folded")
        FLAMEGRAPH_DIR = self._params["FLAMEGRAPH_DIR"]
        desc = "folding stacks"
        if not os.path.isfile(infile):
            return (False, desc + " (perf output missing)")
        cmd = " ".join(
            [
                os.path.join(FLAMEGRAPH_DIR, "stackcollapse-perf.pl"),
                infile, ">", outfile
            ]
        )
        cmd_2 = " ".join(
            [
                os.path.join(FLAMEGRAPH_DIR, "stackcollapse-perf.pl"),
                "--all",
                infile, ">", outfile_annotated
            ]
        )
        p1 = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, _ = p1.communicate()
        p1_2 = subprocess.Popen(
            cmd_2, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        _, _ = p1_2.communicate()
        stat_cmd = f"stat -c %s" if not sys.platform == "darwin" else 'stat -f "%z"'
        p1b = subprocess.Popen(
            " ".join([stat_cmd, outfile]),
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        p1b_stdout, p1b_stderr = p1b.communicate()
        rc = p1.returncode
        if rc > 0:
            return (False, desc + f" (stackcollapse failed with code {rc})")
        if len(p1b_stderr) > 0:
            return (False, desc + " (failed reading output file)")
        if float(p1b_stdout.decode()) < 1:
            return (False, desc + " (output file too small)")
        return (True, desc)

