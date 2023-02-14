import json
import re
from enum import Enum

IMPLEMENTATIONS = {}


class Role(Enum):
    BOTH = "both"
    SERVER = "server"
    CLIENT = "client"


def parse_filesize(input):
    units = {None: 1, "B": 1, "KB": 2 ** 10, "MB": 2 ** 20, "GB": 2 ** 30, "TB": 2 ** 40}
    if isinstance(input, int):
        return input
    m = re.match(r'^(\d+(?:\.\d+)?)\s*([KMGT]?B)?$', input.upper())
    if m:
        number, unit = m.groups()
        return int(float(number) * units[unit])
    raise ValueError("Invalid file size")


with open("implementations.json", "r") as f:
    data = json.load(f)
    for name, val in data.items():
        if 'max_filesize' in val.keys():
            val['max_filesize'] = parse_filesize(val['max_filesize'])
        IMPLEMENTATIONS[name] = val
