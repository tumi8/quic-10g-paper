# QUIC Interop Runner - Postprocessing Pipeline

## 1. Installation

* Install required python modules by running `pip install -r requirements.txt`. 
* [FlameGraph](https://github.com/brendangregg/FlameGraph) is used to generate svg files for visualization. Clone it by running `git clone https://github.com/brendangregg/FlameGraph.git`
* Create a config file with `cp pipeline.ini.example pipeline.ini`. Replace all default path values with the correct ones for your system.

## 2. Usage

### 2.1. Basic Usage

* Run the pipeline with `./pipeline.py` (or `python pipeline.py`)
* Specify the log folders you want to process with one or the following options:
    * Use `-a` or `--all-log-dirs` to process all log directories. This might take a long time, depending on how many log directories you have.
    * Use `-d` or `--log-dir` to process one single log directory, for example `-d logs_2022-01-01T12:00:00`. This is especially useful for fully automated processing.
    * Use none of the above arguments to receive an interactive selection. Use the arrow keys and SPACE to select all log directories you want to process. Press ENTER to continue. This option is especially useful, if you just quickly want to evaluate the last performed measurement. Since the directories are sorted descending, just call the pipeline without arguments, press SPACE and ENTER.
* Wait for the pipeline to complete. After all tasks have been performed, the pipeline will terminate.
* Go to the log directories to look at the newly generated svg files (or other output files).

### 2.2. More Ccnfiguration Options

* Use `-r` or `--all-repetitions` to process all repetitions instead of just the first one.
