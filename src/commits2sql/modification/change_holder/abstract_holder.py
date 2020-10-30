import abc


class AbstractHolder(object):
    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def is_renamed(self):
        pass
