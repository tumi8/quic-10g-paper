# QUIC Interop Runner - Result Parsing
Given a list of locations of logdirs, transform all information in them
into a single csv file using python pandas.

## Requirements
Install packages from `requirements.txt`:
```bash
python3 -m pip install -r requirements.txt
```

## Usage
Help output:
```txt
usage: parser.py [-h] -r ROOTDIRS [ROOTDIRS ...] [-o OUTPUT] [-g] [-c] [-s]

options:
  -h, --help            show this help message and exit
  -r ROOTDIRS [ROOTDIRS ...], --rootdirs ROOTDIRS [ROOTDIRS ...]
                        A list of directories containing logdirs inside them
  -o OUTPUT, --output OUTPUT
                        Where to output the csv file
  -d, --debug           enable DEBUG output
```

## FAQ

### Some ethtool columns are empty
Unfortunately, the output of ethtool looks different on different
systems. If this happens to you, look at the ethtool output files
to retrieve the interesting indexes and insert them into the
parser.

### It threw an `NotImplemented` exception. Why?
We throw this exception if a parser cannot extract its information from
a logdir. This makes the whole run fail. The user has to guarantee that
all logdirs include the parsers needed information.
Such a case would occur if, for example, you want to extract server
CPU utilization information, but you did not capture CPU utilization
information in the interop runner using the pidstat pre/postscript.

### I want to extract my own custom information into a column
1. Create a parser which inherits from the abstract class `Parser`.
   Implement the function `columnheader()`, to give the column a name, and
   the function `parse()` to extract information from a logdir.
   The `parse()` function is executed for each implementation pair in the logdir
   and for each repetition, which is mirrored in its parameters (the logdir,
   the implementation pair and the current repetition).
2. Add your parser to the scripts argument parsing and make sure it is
   propagated to the iteration function like the other parsers.

## Known issues
- You have to manually make sure the directories fulfill the requirements
  for the parsers. Else, a `NotImplemented` exception is thrown.
  E.g., for server CPU utilizationm info, the interop runner had to be executed
  using the pidstat pre/postscript to create a `pidstat.txt` file in each
  repetition directory.
