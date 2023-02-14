import os
from enum import Enum
from urllib.parse import urlparse


class Testcase(Enum):
    HANDSHAKE = 1
    TRANSFER = 2
    VERSION_NEGOTIATION = 3
    MULTI_HANDSHAKE = 4
    CHACHA_20 = 5
    TRANSPORT_PARAMETER = 6
    RETRY = 7
    RESUMPTION = 8
    ZERO_RTT = 9
    M_GOODPUT = 10
    M_QLOG = 11
    M_OPTIMIZE = 12

    @staticmethod
    def from_string(string):
        mapping = {
            'handshake': Testcase.HANDSHAKE,
            'transfer': Testcase.TRANSFER,
            'versionnegotiation': Testcase.VERSION_NEGOTIATION,
            'multihandshake': Testcase.MULTI_HANDSHAKE,
            'chacha20': Testcase.CHACHA_20,
            'transportparameter': Testcase.TRANSPORT_PARAMETER,
            'retry': Testcase.RETRY,
            'resumption': Testcase.RESUMPTION,
            'zerortt': Testcase.ZERO_RTT,
            'goodput': Testcase.M_GOODPUT,
            'qlog': Testcase.M_QLOG,
            'optimize': Testcase.M_OPTIMIZE,
        }
        if string not in mapping.keys():
            raise ValueError(f'Unknown testcase {string}')
        return mapping.get(string)


class URL:
    def __init__(self, url: str) -> None:
        parsed = urlparse(url)

        self.authority = parsed.netloc
        self.full_path = parsed.path
        if parsed.query:
            self.full_path += "?" + parsed.query
        self.scheme = parsed.scheme

    @staticmethod
    def from_string(request):
        return urlparse(request)


def environ_or_required(key, required=True, default=None):
    default = os.getenv(key, default)
    if default is not None:
        return {'default': default, 'required': False}
    else:
        return {'required': required}


def mkdirs(path):
    directory = os.path.dirname(path)
    if directory and not os.path.exists(directory):
        os.makedirs(directory)
