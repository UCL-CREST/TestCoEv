import math
from typing import Dict, Tuple

from evaluator4link.measurements.with_ground_truth import (
    StrategyWithGroundTruthMeasurement,
)
from evaluator4link.measurements.utils import GroundTruthMethodName, DatabaseMethodName


class MeanAbsoluteAndSquaredErrorMeasurement(StrategyWithGroundTruthMeasurement):

    __SELECT_ALL_CANDIDATE_WITH_SCORE_SQL = """
        WITH alive_methods AS (
            SELECT id, simple_name AS name, class_name, file_path FROM methods
            WHERE NOT EXISTS(
                SELECT target_method_id FROM changes
                WHERE change_type = 'REMOVE' and target_method_id = id
            )
        ), candidate_test AS (
            SELECT id, name FROM alive_methods
            WHERE name LIKE :test_simple_name 
            AND class_name = :test_class 
            AND file_path LIKE :test_path
        ), candidate_tested AS (
            SELECT id, name FROM alive_methods
            WHERE name LIKE :tested_simple_name 
            AND class_name = :tested_class 
            AND file_path LIKE :tested_path
        )
        SELECT candidate_test.name, candidate_tested.name, confidence_num FROM (
            candidate_test 
            INNER JOIN candidate_tested 
            INNER JOIN {strategy_name}
            ON tested_method_id = candidate_tested.id 
            AND test_method_id = candidate_test.id
        )
    """

    def __init__(self, path_to_db: str, path_to_csv: str, for_strategy: str):
        self.__map_for_score: Dict[Tuple[str, str], float] = dict()
        self.__strategy_name = for_strategy
        super().__init__(path_to_db, path_to_csv)

    def _measure(self) -> None:
        for row in self._ground_truth_pandas.itertuples():
            test, tested = GroundTruthMethodName(row[1]), GroundTruthMethodName(row[2])
            signatures_key = (tested.long_name, test.long_name)
            predicate_score = self.__get_predicate_score(test, tested)
            self.__map_for_score[signatures_key] = predicate_score
        return None

    def __get_predicate_score(
        self, test: GroundTruthMethodName, tested: GroundTruthMethodName
    ) -> float:
        cursor = self._predict_database.cursor()
        select_sql = self.__SELECT_ALL_CANDIDATE_WITH_SCORE_SQL.format(
            strategy_name=self.__strategy_name
        )
        possible_link = cursor.execute(
            select_sql,
            {
                "test_simple_name": f"{test.simple_name}%",
                "test_class": test.class_name,
                "test_path": f"%{test.file_path}%",
                "tested_simple_name": f"{tested.simple_name}%",
                "tested_class": tested.class_name,
                "tested_path": f"%{tested.file_path}%",
            },
        )

        for test_candidate, tested_candidate, confidence in possible_link:
            pd_name_test = DatabaseMethodName(
                test.file_path, test.class_name, test_candidate
            )
            pd_name_tested = DatabaseMethodName(
                tested.file_path, tested.class_name, tested_candidate
            )
            if pd_name_test.signature != test.signature:
                continue
            if pd_name_tested.signature != tested.signature:
                continue
            return confidence
        cursor.close()
        return 0.0

    @property
    def mean_absolute_error(self) -> float:
        sum = 0.0
        count = len(self.__map_for_score)
        for _, confidence in self.__map_for_score.items():
            sum += 1.0 - confidence
        return sum / count

    @property
    def root_mean_squared_absolute(self) -> float:
        root_sum = 0.0
        count = len(self.__map_for_score)
        for _, confidence in self.__map_for_score.items():
            root_sum += (1.0 - confidence) ** 2
        return math.sqrt(root_sum / count)

    @property
    def mean_absolute_percentage_error(self) -> float:
        percent_sum = 0.0
        count = len(self.__map_for_score)
        for _, confidence in self.__map_for_score.items():
            percent_sum += (1.0 - confidence) / 1.0
        return percent_sum / count

    @property
    def predicted_co_change_confidences(self) -> Dict[Tuple[str, str], float]:
        return self.__map_for_score

    def __str__(self):
        return str(
            {
                "mean_absolute_error": self.mean_absolute_error,
                "root_mean_squared_absolute": self.root_mean_squared_absolute,
                "mean_absolute_percentage_error": self.mean_absolute_percentage_error,
                "values": self.__map_for_score,
            }
        )
