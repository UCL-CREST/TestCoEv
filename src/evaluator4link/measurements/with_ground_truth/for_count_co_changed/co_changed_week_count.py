from typing import Dict, List
from evaluator4link.measurements.with_ground_truth import (
    StrategyWithGroundTruthMeasurement,
)
from evaluator4link.measurements.utils import GroundTruthMethodName


class CoChangedWeekCountMeasurement(StrategyWithGroundTruthMeasurement):
    @property
    def __select_co_changed_weeks_sql_stmt(self) -> str:
        return """
        WITH commits_to_weeks AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash  FROM git_commits
        ),
        changes_week_based AS (
            SELECT target_method_id, change_type, week AS change_week FROM (
                git_changes INNER JOIN commits_to_weeks
                ON git_changes.commit_hash = commits_to_weeks.commit_hash
            )
        ),
        methods_test AS (
            SELECT id AS test_id FROM git_methods
            WHERE file_path LIKE 'src/test/java/org/apache/commons/lang3/%'
        ), 
        functions_tested AS (
            SELECT id AS tested_id FROM git_methods
            WHERE file_path LIKE 'src/main/java/org/apache/commons/lang3/%'
        )
        SELECT change_week FROM changes_week_based WHERE target_method_id IN methods_test
        INTERSECT 
        SELECT change_week FROM changes_week_based WHERE target_method_id IN functions_tested
    """

    @property
    def __select_co_changed_tested_with_weeks_sql_stmt(self) -> str:
        return """
        UNFINISHED
    """

    @property
    def __select_co_changed_test_with_commits_sql_stmt(self) -> str:
        return """
        UNFINISHED
    """

    @property
    def commits_ground_truth(self) -> Dict[int, int]:
        pass

    @property
    def commit_predicted_co_changed_for_test(self) -> Dict[int, int]:
        pass

    @property
    def commit_predicted_co_changed_for_tested(self) -> Dict[int, int]:
        pass

    def __init__(self, path_to_db: str, path_to_csv: str):
        pass

    def _measure(self) -> None:
        pass

    def __get_co_changed_commits_for(self, test_id: int, tested_id: int) -> List[int]:
        pass

    def __get_predicted_co_changed_commits_for(
        self, sql_stmt: str, parameters: Dict[str, int]
    ) -> List[int]:
        pass

    def __from_commits_to_x(self, hash_value: str) -> int:
        pass
