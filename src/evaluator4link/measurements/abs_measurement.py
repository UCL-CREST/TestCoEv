import abc
import sqlite3
from typing import Optional, Any


class AbstractMeasurement(object):
    __metaclass__ = abc.ABCMeta
    __FLYWEIGHT_PREDICT_DB: Optional[sqlite3.Connection] = None

    def __init__(self, path_to_db: str):
        if self.__FLYWEIGHT_PREDICT_DB is None:
            self.__FLYWEIGHT_PREDICT_DB = sqlite3.connect(path_to_db)
        self._measure()

    @property
    def _predict_database(self) -> sqlite3.Connection:
        return self.__FLYWEIGHT_PREDICT_DB

    @abc.abstractmethod
    def _measure(self) -> Any:
        pass
