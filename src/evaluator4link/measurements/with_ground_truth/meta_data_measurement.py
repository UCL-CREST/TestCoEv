import logging
from typing import Dict, Tuple, Optional

import pandas

from evaluator4link.measurements import AbstractMeasurement
from evaluator4link.measurements.utils import GroundTruthMethodName, DatabaseMethodName


class StrategyWithGroundTruthMeasurement(AbstractMeasurement):

    __SELECT_CANDIDATE_ID_SQL = """
        WITH valid_methods AS (
            SELECT id, simple_name, class_name, file_path FROM git_methods
            WHERE NOT EXISTS(
                SELECT target_method_id FROM git_changes
                WHERE change_type = 'REMOVE' AND target_method_id = id
            )
            AND simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        )
        SELECT id, simple_name, class_name, file_path FROM valid_methods
        WHERE simple_name LIKE :simple_name
        AND class_name LIKE :class_name
        AND file_path LIKE :file_path
    """

    __SELECT_PREDICT_FOR_SAME_ID = """
        SELECT tested_method_id, test_method_id, confidence_num FROM {strategy}
        WHERE tested_method_id = :method_id OR test_method_id = :method_id
    """

    __SELECT_METHOD_BY_ID_SQL_STMT = """
        SELECT simple_name, class_name, file_path FROM git_methods
        WHERE id = :method_id
    """

    __FLYWEIGHT_TRUTH_PANDAS: Optional[pandas.DataFrame] = None

    @property
    def _ground_truth_pandas(self) -> pandas.DataFrame:
        return self.__FLYWEIGHT_TRUTH_PANDAS

    def __init__(self, path_to_db: str, path_to_csv: str, for_strategy: str):
        if self.__FLYWEIGHT_TRUTH_PANDAS is None:
            self.__FLYWEIGHT_TRUTH_PANDAS = pandas.read_csv(path_to_csv)
        self.__strategy_name = for_strategy
        self._predict_links: Dict[Tuple[int, int], float] = dict()
        self._ground_truth_links: Dict[Tuple[int, int], float] = dict()
        self._valid_predict_links: Dict[Tuple[int, int], float] = dict()
        self._method_name_id_dict: Dict[str, int] = dict()
        super().__init__(path_to_db)

    def _measure(self) -> None:
        for row in self._ground_truth_pandas.itertuples():
            test, tested = GroundTruthMethodName(row[1]), GroundTruthMethodName(row[2])
            test_id, tested_id = self.get_method_id_by_(test), self.get_method_id_by_(
                tested
            )
            self._ground_truth_links[(tested_id, test_id)] = 1.0
        for (tested_id, test_id) in self._ground_truth_links.keys():
            links_for_class = self.__get_predicate_links_of(test_id)
            self._predict_links.update(links_for_class)
        predicted_links_set = set(self._predict_links.keys())
        ground_truth_links_set = set(self._ground_truth_links.keys())
        valid_predict_links_set = predicted_links_set.intersection(
            ground_truth_links_set
        )
        self._valid_predict_links = {
            names: self._predict_links[names] for names in valid_predict_links_set
        }
        return None

    def get_method_id_by_(self, gt_name: GroundTruthMethodName) -> Optional[int]:
        if gt_name.long_name in self._method_name_id_dict:
            return self._method_name_id_dict[gt_name.long_name]
        cursor = self._predict_database.cursor()
        select_sql = self.__SELECT_CANDIDATE_ID_SQL.format(
            strategy=self.__strategy_name
        )
        candidates_methods = cursor.execute(
            select_sql,
            {
                "simple_name": f"{gt_name.simple_name}%",
                "class_name": f'{gt_name.class_name.replace("::", "%::")}%',
                "file_path": f"%{gt_name.file_path}%",
            },
        )
        for (
            method_id,
            long_name,
            class_name,
            file_path,
        ) in candidates_methods.fetchall():
            db_name = DatabaseMethodName(file_path, class_name, long_name)
            if db_name.signature != gt_name.signature:
                continue
            self._method_name_id_dict[gt_name.long_name] = method_id
            return method_id
        logging.warning(
            f'cannot find out method "{gt_name.long_name}" from the database. '
        )
        return None

    def get_method_name_by_id(self, method_id: int) -> Optional[str]:
        for stored_name, stored_id in self._method_name_id_dict.items():
            if stored_id == method_id:
                return stored_name
        cursor = self._predict_database.cursor()
        select_sql = self.__SELECT_METHOD_BY_ID_SQL_STMT
        method_name, method_class, method_file = cursor.execute(
            select_sql, {"method_id": method_id}
        ).fetchall()
        name_from_db = DatabaseMethodName(
            method_file, method_class, method_name
        ).package_name_with_signature
        self._method_name_id_dict[name_from_db] = method_id
        return name_from_db

    def __get_predicate_links_of(self, method_id: int) -> Dict[Tuple[int, int], float]:
        output = dict()
        cursor = self._predict_database.cursor()
        select_sql = self.__SELECT_PREDICT_FOR_SAME_ID.format(
            strategy=self.__strategy_name
        )
        all_links = cursor.execute(select_sql, {"method_id": method_id}).fetchall()
        for tested_id, test_id, confidence_num in all_links:
            output[(tested_id, test_id)] = confidence_num
        return output

    @property
    def predict_links(self) -> Dict[Tuple[int, int], float]:
        return self._predict_links

    @property
    def ground_truth_links(self) -> Dict[Tuple[int, int], float]:
        return self._ground_truth_links

    @property
    def valid_predict_links(self) -> Dict[Tuple[int, int], float]:
        return self._valid_predict_links
