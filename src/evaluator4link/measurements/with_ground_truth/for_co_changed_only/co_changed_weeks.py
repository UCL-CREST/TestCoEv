from typing import List, Dict, Tuple, Set
from evaluator4link.measurements.with_ground_truth.for_co_changed_only import (
    AbstractCoChangeMetaDataMeasurement,
)


class CoChangedWeeksMeasurement(AbstractCoChangeMetaDataMeasurement):
    @property
    def _select_method_changes_sql_stmt(self) -> str:
        return """
        WITH week_commit_table AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash FROM git_commits
        ),
        week_based_changes AS (
            SELECT target_method_id, week AS change_week FROM (
                git_changes INNER JOIN week_commit_table
                ON git_changes.commit_hash = week_commit_table.commit_hash
            )
        )
        SELECT DISTINCT change_week FROM week_based_changes
        WHERE target_method_id = :method_id
    """

    @property
    def test_changed_weeks(self) -> Dict[int, Set[int]]:
        return self.__test_changed_weeks

    @property
    def tested_changed_weeks(self) -> Dict[int, Set[int]]:
        return self.__tested_changed_weeks

    @property
    def co_changes_weeks(self) -> Dict[int, Set[int]]:
        return self.__co_changed_weeks

    @property
    def commit_week_to_id_mapping(self) -> Dict[str, int]:
        return self.__weeks_num_id_mapping

    def __init__(self, path_to_db: str, path_to_csv: str):
        super().__init__(path_to_db, path_to_csv, "co_changed_for_weeks")
        self.__weeks_num_id_mapping: Dict[str, int] = dict()
        self.__test_changed_weeks = {
            method_id: {
                self.__from_hash_value_to_id(change_week)
                for change_week in change_weeks
            }
            for method_id, change_weeks in self._test_changes.items()
        }
        self.__tested_changed_weeks = {
            method_id: {
                self.__from_hash_value_to_id(change_week)
                for change_week in change_weeks
            }
            for method_id, change_weeks in self._tested_changes.items()
        }
        self.__co_changed_weeks = {
            method_pair: {
                self.__from_hash_value_to_id(change_week)
                for change_week in change_weeks
            }
            for method_pair, change_weeks in self._co_changes.items()
        }

    def __from_hash_value_to_id(self, hash_val: str) -> int:
        self.__weeks_num_id_mapping.setdefault(
            hash_val, len(self.__weeks_num_id_mapping) + 1
        )
        return self.__weeks_num_id_mapping[hash_val]

    def __str__(self):
        return str(
            {
                "test_changed_weeks": self.__test_changed_weeks,
                "tested_changed_weeks": self.__tested_changed_weeks,
                "co_changed_weeks": self.__co_changed_weeks,
                "weeks_num_id_mapping": self.__weeks_num_id_mapping,
            }
        )
