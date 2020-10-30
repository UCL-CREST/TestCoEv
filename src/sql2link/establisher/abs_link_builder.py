import abc
import logging
import sqlite3
from typing import Optional, List, Dict


class AbsLinkEstablisher(object):
    __metaclass__ = abc.ABCMeta

    def __init__(self, db_path: str):
        self.__connector = sqlite3.connect(db_path.replace("-", "_"))

    def do(
        self,
        parameters: Optional[Dict] = None,
        is_previous_ingored: bool = False,
        is_verbose_model: bool = False,
    ) -> None:
        sql_parameters = {"test_path": "src/test%", "tested_path": "src/main%"}
        if parameters is not None:
            sql_parameters.update(parameters)
        try:
            cursor = self.__connector.cursor()
            if is_previous_ingored:
                cursor.execute(self._remove_previous_table_sql)
            cursor.execute(self._initial_table_sql)
            cursor.execute(self._link_establishing_sql, sql_parameters)
            for row in cursor.fetchall():
                if is_verbose_model:
                    print(row)
                cursor.execute(self._insert_new_row_sql, row)
            cursor.close()
            self.__connector.commit()
        except sqlite3.Error as error:
            logging.warning(f"exit because of the crash {error}")
        return None

    @property
    @abc.abstractmethod
    def _remove_previous_table_sql(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def _initial_table_sql(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def _insert_new_row_sql(self) -> str:
        pass

    @property
    @abc.abstractmethod
    def _link_establishing_sql(self) -> str:
        pass
