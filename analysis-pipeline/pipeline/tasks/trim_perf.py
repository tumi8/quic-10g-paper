import os
import io
import shutil

from .abstract_task import Task

class TrimPerf(Task):

    @staticmethod
    def desc():
        return "Trimming perf file..."

    def run(self):
        """
        Expects the following parameters in the params dict:
        dir: the directory containing out.perf
        """
        dir = self._params["dir"]
        suffix = self._params["suffix"]
        infile = os.path.join(dir, "out.perf")
        outfile = os.path.join(dir, "out.perf.trimmed")

        desc = "trimming perf file"

        if not os.path.isfile(infile):
            return (False, desc + f" (perf output ({infile}) missing)")
        
        with open(infile) as fin:
            entries = 0
            last_one_empty = True
            write_to_buffer = False
            buffer = io.StringIO()
            fout = open(outfile,"w")
            timespan = [0, 0]
            transmission_timespan = [0, 0]
            lines_written = [0, 0]
            transmission_has_started = False
            lines = 0
            for i, line in enumerate(fin):
                if not line.strip(): # line is empty
                    if last_one_empty:
                        lines = i
                        break
                    else:
                        lines = i
                        last_one_empty = True
                else: # line contains data
                    if last_one_empty:
                        entries += 1
                        split = line.split()
                        l = len(split)
                        name, time = (" ").join(split[0:l-5]), split[l-3]
                        time = int(time.replace(":", "").replace(".", ""))

                        if timespan[0] == 0:
                            timespan[0] = time
                        timespan[1] = time

                        if name == ("http_"+suffix) or name == ("quiche-"+suffix):
                            # update transmission started state and transmission timespan
                            if not transmission_has_started:
                                transmission_has_started = True
                                transmission_timespan[0] = time
                            transmission_timespan[1] = time
                            write_to_buffer = False
                        else:
                            write_to_buffer = True
                        last_one_empty = False

                # line contains data
                if transmission_has_started:
                    if not write_to_buffer:
                        # write to out file, copy buffer to file if not empty
                        buffer.seek(0)
                        shutil.copyfileobj(buffer, fout)
                        buffer = io.StringIO()
                        fout.write(line)
                        if lines_written[0] == 0:
                            lines_written[0] = i
                        lines_written[1] = i
                    else:
                        # write to buffer
                        buffer.write(line)
            fout.close()           

            #print(f"Trimming perf file...")
            #print(f"Found {entries} samples")
            #print(f"Removed lines 1 to {lines_written[0]} and {lines_written[1]+2} to {lines+1}")
            #print(f"This equals {(transmission_timespan[0] - timespan[0]) / 1000000} s before and {(timespan[1] - transmission_timespan[1]) / 1000000} s after transmission")
            #print(f"Perf Capture Duration: {(timespan[1] - timespan[0]) / 1000000} seconds")
            #print(f"Transmission Duration: {(transmission_timespan[1] - transmission_timespan[0]) / 1000000} seconds")
        return (True, f"Removed {(transmission_timespan[0] - timespan[0]) / 1000000} s before and {(timespan[1] - transmission_timespan[1]) / 1000000} s after transmission")