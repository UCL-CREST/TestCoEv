import abc


class AbsMethodNameExtractor(object):
    __metaclass__ = abc.ABCMeta

    @property
    @abc.abstractmethod
    def simple_name(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def signature(self) -> str:
        pass
