import abc
import re

from utils import log_task

class Task(abc.ABC):
    _suffix = None
    _params = {}

    def __init__(
        self,
        params = {},
        suffix = None,
    ):
        self._suffix = params.get("suffix")
        if suffix:
            self._suffix = suffix
        self._params = params

    def name(self):
        """ The class name in snake case is the default value. """
        return "_".join(filter(None, [re.sub(r'(?<!^)(?=[A-Z])', '_', type(self).__name__).lower(), self._suffix]))

    @abc.abstractmethod
    def desc(self):
        pass

    @abc.abstractmethod
    def run(self):
        pass

    def run_and_log(self):
        status, message = self.run()
        log_task("[" + self.name() + "] " + message, 4, status)
        return status

    def __str__(self):
        return self.name()
