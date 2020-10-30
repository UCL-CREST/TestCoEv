from typing import Dict, List
from evaluator4link.measurements.with_ground_truth import (
    StrategyWithGroundTruthMeasurement,
)
from evaluator4link.measurements.utils import GroundTruthMethodName


class CoChangedCommitCountMeasurement(StrategyWithGroundTruthMeasurement):
    @property
    def __select_co_changed_commits_sql_stmt(self) -> str:
        return """
        WITH test_commits AS (
            SELECT target_method_id AS test_id, commit_hash FROM git_changes
            WHERE target_method_id = :test_method_id
        ), tested_commits AS (
            SELECT target_method_id AS tested_id, commit_hash FROM git_changes
            WHERE target_method_id = :tested_method_id
        )
        SELECT test_commits.commit_hash FROM (
            test_commits INNER JOIN tested_commits
            ON test_commits.commit_hash = tested_commits.commit_hash
        )
    """

    @property
    def __select_co_changed_tested_with_commits_sql_stmt(self) -> str:
        return """
        WITH co_changed_ids AS (
            SELECT test_method_id, tested_method_id FROM links_commits_based_cochanged
            WHERE test_method_id = :test_method_id
        ), test_commits AS (
            SELECT target_method_id AS test_id, commit_hash FROM git_changes
            WHERE target_method_id = :test_method_id
        ), tested_commits AS (
            SELECT target_method_id AS tested_id, commit_hash FROM (
                git_changes INNER JOIN co_changed_ids
                ON target_method_id = co_changed_ids.tested_method_id
            )
        )
        SELECT test_commits.commit_hash, tested_id FROM (
            test_commits INNER JOIN tested_commits
            ON test_commits.commit_hash = tested_commits.commit_hash
        )
    """

    @property
    def __select_co_changed_test_with_commits_sql_stmt(self) -> str:
        return """
        WITH co_changed_ids AS (
            SELECT test_method_id, tested_method_id FROM links_commits_based_cochanged
            WHERE tested_method_id = :tested_method_id
        ), tested_commits AS (
            SELECT target_method_id AS tested_id, commit_hash FROM git_changes
            WHERE target_method_id = :tested_method_id
        ), test_commits AS (
            SELECT target_method_id AS test_id, commit_hash FROM (
                git_changes INNER JOIN co_changed_ids
                ON target_method_id = co_changed_ids.test_method_id
            )
        )
        SELECT test_commits.commit_hash, test_id FROM (
            test_commits INNER JOIN tested_commits
            ON test_commits.commit_hash = tested_commits.commit_hash
        )
    """

    @property
    def commits_ground_truth(self) -> Dict[int, int]:
        return self.__commits_ground_truth_co_changed

    @property
    def commit_predicted_co_changed_for_test(self) -> Dict[int, int]:
        return self.__commits_predicted_co_change_for_test

    @property
    def commit_predicted_co_changed_for_tested(self) -> Dict[int, int]:
        return self.__commits_predicted_co_change_for_tested

    def __init__(self, path_to_db: str, path_to_csv: str):
        self.__commits_ground_truth_co_changed: Dict[
            int, int
        ] = dict()  # commit, number of ground truths
        self.__commits_predicted_co_change_for_test: Dict[int, int] = dict()
        self.__commits_predicted_co_change_for_tested: Dict[int, int] = dict()
        self.__commit_x_mapping: Dict[str, int] = dict()
        super().__init__(path_to_db, path_to_csv, "links_co_changed_for_commits")

    def _measure(self) -> None:
        tested_id_set, test_id_set = set(), set()
        for row in self._ground_truth_pandas.itertuples():
            test, tested = GroundTruthMethodName(row[1]), GroundTruthMethodName(row[2])
            test_id, tested_id = self.get_method_id_by_(test), self.get_method_id_by_(
                tested
            )
            for commit in self.__get_co_changed_commits_for(test_id, tested_id):
                self.__commits_ground_truth_co_changed.setdefault(commit, 0)
                self.__commits_ground_truth_co_changed[commit] += 1
            test_id_set.add(test_id)
            tested_id_set.add(tested_id)
        for test_id in test_id_set:
            sql_stmt = self.__select_co_changed_tested_with_commits_sql_stmt
            for commit in self.__get_predicted_co_changed_commits_for(
                sql_stmt, {"test_method_id": test_id}
            ):
                self.__commits_predicted_co_change_for_test.setdefault(commit, 0)
                self.__commits_predicted_co_change_for_test[commit] += 1
        for tested_id in tested_id_set:
            sql_stmt = self.__select_co_changed_test_with_commits_sql_stmt
            for commit in self.__get_predicted_co_changed_commits_for(
                sql_stmt, {"tested_method_id": tested_id}
            ):
                self.__commits_predicted_co_change_for_tested.setdefault(commit, 0)
                self.__commits_predicted_co_change_for_tested[commit] += 1
        return None

    def __get_co_changed_commits_for(self, test_id: int, tested_id: int) -> List[int]:
        cursor = self._predict_database.cursor()
        exe_res = cursor.execute(
            self.__select_co_changed_commits_sql_stmt,
            {"test_method_id": test_id, "tested_method_id": tested_id},
        )
        output = [self.__from_commits_to_x(row[0]) for row in exe_res.fetchall()]
        cursor.close()
        return output

    def __get_predicted_co_changed_commits_for(
        self, sql_stmt: str, parameters: Dict[str, int]
    ) -> List[int]:
        cursor = self._predict_database.cursor()
        exe_res = cursor.execute(sql_stmt, parameters)
        output = [self.__from_commits_to_x(row[0]) for row in exe_res.fetchall()]
        cursor.close()
        return output

    def __from_commits_to_x(self, hash_value: str) -> int:
        if hash_value not in self.__commit_x_mapping:
            self.__commit_x_mapping[hash_value] = len(self.__commit_x_mapping) + 1
        return self.__commit_x_mapping[hash_value]
