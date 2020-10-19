import abc
from typing import Dict, Tuple, Set

from evaluator4link.measurements.with_ground_truth import StrategyWithGroundTruthMeasurement


class AbstractCoChangeMetaDataMeasurement(StrategyWithGroundTruthMeasurement):

    __metaclass__ = abc.ABCMeta

    @property
    @abc.abstractmethod
    def _select_method_changes_sql_stmt(self) -> str: pass

    @property
    def _test_changes(self) -> Dict[int, Set[str]]:
        return self.__test_changes

    @property
    def _tested_changes(self) -> Dict[int, Set[str]]:
        return self.__tested_changes

    @property
    def _co_changes(self) -> Dict[Tuple[int, int], Set[str]]:
        return self.__co_changes

    def __init__(self, path_to_db: str, path_to_csv: str, for_strategy: str):
        self.__test_changes: Dict[int, Set[str]] = dict()
        self.__tested_changes: Dict[int, Set[str]] = dict()
        self.__co_changes: Dict[Tuple[int, int], Set[str]] = dict()
        super().__init__(path_to_db, path_to_csv, for_strategy)

    def _measure(self) -> None:
        super(AbstractCoChangeMetaDataMeasurement, self)._measure()
        test_ids, tested_ids = list(), list()
        for tested_id, test_id in self._ground_truth_links.keys():
            test_ids.append(test_id)
            tested_ids.append(tested_id)
        self.__test_changes.update(self.__query_changes_records(test_ids))
        self.__tested_changes.update(self.__query_changes_records(tested_ids))
        for tested_id, test_id in self._ground_truth_links.keys():
            co_change_pair = (tested_id, test_id)
            co_changes = set(self.__test_changes[test_id]) & set(self.__tested_changes[tested_id])
            self._co_changes[co_change_pair] = co_changes
        return None

    def __query_changes_records(self, method_ids) -> Dict[int, Set[str]]:
        db_cursor = self._predict_database.cursor()
        output: Dict[int, Set[str]] = dict()
        for method_id in method_ids:
            if method_id in output: continue
            exe_result = db_cursor.execute(self._select_method_changes_sql_stmt, {'method_id': method_id})
            output[method_id] = {row[0] for row in exe_result if exe_result is not None and len(row) >= 1}
        db_cursor.close()
        return output

    def __str__(self):
        return str({
            'test_changes': self.__test_changes,
            'tested_changes': self.__tested_changes,
            'co_changes': self.__co_changes
        })
