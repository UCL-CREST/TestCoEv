import abc
from typing import Dict, List, Tuple
from evaluator4link.measurements import AbstractMeasurement


class AbstractWeeksCountMeasurement(AbstractMeasurement):
    __metaclass__ = abc.ABCMeta

    @property
    @abc.abstractmethod
    def _count_changes_in_week_sql_stmt(self) -> str:
        pass

    @property
    def weeks_xs_mapping(self) -> Dict[str, int]:
        return self.__week_xs_table

    @property
    def type_zs_mapping(self) -> Dict[str, int]:
        return self.__type_zs_table

    @property
    def weeks_count_coordinates(self) -> List[Tuple[int, int, int]]:
        return self.__week_change_counts

    def __init__(self, path_to_db: str):
        self.__week_xs_table: Dict[str, int] = dict()
        self.__type_zs_table: Dict[str, int] = {
            "ADD": 1,
            "MODIFY": 2,
            "RENAME": 3,
            "REMOVE": 4,
        }
        self.__week_change_counts: List[Tuple[int, int, int]] = list()
        super().__init__(path_to_db)

    def _measure(self) -> None:
        cursor = self._predict_database.cursor()
        exe_res = cursor.execute(self._count_changes_in_week_sql_stmt)
        for week_hash, change_type, change_count in exe_res:
            x_val = self.__from_hash_to_x_value(week_hash)
            y_val = change_count
            z_val = self.__from_change_type_to_y_value(change_type)
            self.__week_change_counts.append((x_val, y_val, z_val))
        cursor.close()
        return None

    def __from_hash_to_x_value(self, hash_value: str) -> int:
        if hash_value not in self.__week_xs_table:
            self.__week_xs_table[hash_value] = len(self.__week_xs_table) + 1
        return self.__week_xs_table[hash_value]

    def __from_change_type_to_y_value(self, change_type: str) -> int:
        return self.__type_zs_table[change_type]


class FileWeeksCountMeasurement(AbstractWeeksCountMeasurement):
    @property
    def _count_changes_in_week_sql_stmt(self) -> str:
        return """
        WITH commits_to_weeks AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash  FROM git_commits
        ),
        changes_week_based AS (
            SELECT target_method_id, change_type, week AS change_week FROM (
                git_changes INNER JOIN commits_to_weeks
                ON git_changes.commit_hash = commits_to_weeks.commit_hash
            )
        ), files_changes AS (
            SELECT DISTINCT change_week, change_type, file_path FROM (
                changes_week_based INNER JOIN git_methods
                ON changes_week_based.target_method_id =  git_methods.id
            )
        ), test_files AS (
            SELECT DISTINCT file_path FROM git_methods
            WHERE file_path LIKE 'src/test/java/org/apache/commons/lang3%'
        ), tested_files AS (
            SELECT DISTINCT file_path FROM git_methods
            WHERE file_path LIKE 'src/main/java/org/apache/commons/lang3%'
        ), co_changed_weeks AS (
            SELECT change_week FROM files_changes WHERE file_path IN test_files
            INTERSECT
            SELECT change_week FROM files_changes WHERE file_path IN tested_files
        )
        SELECT change_week, change_type, COUNT(*) FROM files_changes
        WHERE change_week IN co_changed_weeks
        GROUP BY change_week, change_type
    """


class ClassWeeksCountMeasurement(AbstractWeeksCountMeasurement):
    @property
    def _count_changes_in_week_sql_stmt(self) -> str:
        return """
        WITH commits_to_weeks AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash  FROM git_commits
        ),
        changes_week_based AS (
            SELECT target_method_id, change_type, week AS change_week FROM (
                git_changes INNER JOIN commits_to_weeks
                ON git_changes.commit_hash = commits_to_weeks.commit_hash
            )
        ), classes_changes AS (
            SELECT DISTINCT change_week, change_type, (file_path || class_name) AS unique_class_id FROM (
                changes_week_based INNER JOIN git_methods
                ON changes_week_based.target_method_id =  git_methods.id
            )
        ), test_classes AS (
            SELECT DISTINCT (file_path || class_name) AS unique_class_id FROM git_methods
            WHERE file_path LIKE 'src/test/java/org/apache/commons/lang3%'
        ), tested_classes AS (
            SELECT DISTINCT (file_path || class_name) AS unique_class_id FROM git_methods
            WHERE file_path LIKE 'src/main/java/org/apache/commons/lang3%'
        ), co_changed_weeks AS (
            SELECT change_week FROM classes_changes WHERE unique_class_id IN test_classes
            INTERSECT
            SELECT change_week FROM classes_changes WHERE unique_class_id IN tested_classes
        )
        SELECT change_week, change_type, COUNT(*) FROM classes_changes
        WHERE change_week IN co_changed_weeks
        GROUP BY change_week, change_type
    """


class MethodWeeksCountMeasurement(AbstractWeeksCountMeasurement):
    @property
    def _count_changes_in_week_sql_stmt(self) -> str:
        return """
        WITH commits_to_weeks AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash  FROM git_commits
        ),
        changes_week_based AS (
            SELECT DISTINCT target_method_id, change_type, week AS change_week FROM (
                git_changes INNER JOIN commits_to_weeks
                ON git_changes.commit_hash = commits_to_weeks.commit_hash
            )
        ),test_methods AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE 'src/test/java/org/apache/commons/lang3%'
        ), tested_functions AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE 'src/main/java/org/apache/commons/lang3%'
        ), co_changed_weeks AS (
            SELECT change_week FROM changes_week_based WHERE target_method_id IN test_methods
            INTERSECT
            SELECT change_week FROM changes_week_based WHERE target_method_id IN tested_functions
        )
        SELECT change_week, change_type, COUNT(*) FROM changes_week_based
        WHERE change_week IN co_changed_weeks
        GROUP BY change_week, change_type
    """


class TestedWeeksCountMeasurement(AbstractWeeksCountMeasurement):
    @property
    def _count_changes_in_week_sql_stmt(self) -> str:
        return """
        WITH commits_to_weeks AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash  FROM git_commits
        ),
        changes_week_based AS (
            SELECT DISTINCT target_method_id, change_type, week AS change_week FROM (
                git_changes INNER JOIN commits_to_weeks
                ON git_changes.commit_hash = commits_to_weeks.commit_hash
            )
        ),test_methods AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE 'src/test/java/org/apache/commons/lang3%'
        ), tested_functions AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE 'src/main/java/org/apache/commons/lang3%'
        ), co_changed_weeks AS (
            SELECT change_week FROM changes_week_based WHERE target_method_id IN test_methods
            INTERSECT
            SELECT change_week FROM changes_week_based WHERE target_method_id IN tested_functions
        )
        SELECT change_week, change_type, COUNT(*) FROM changes_week_based
        WHERE change_week IN co_changed_weeks AND target_method_id IN tested_functions
        GROUP BY change_week, change_type
    """


class TestWeeksCountMeasurement(AbstractWeeksCountMeasurement):
    @property
    def _count_changes_in_week_sql_stmt(self) -> str:
        return """
        WITH commits_to_weeks AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash  FROM git_commits
        ),
        changes_week_based AS (
            SELECT DISTINCT target_method_id, change_type, week AS change_week FROM (
                git_changes INNER JOIN commits_to_weeks
                ON git_changes.commit_hash = commits_to_weeks.commit_hash
            )
        ),test_methods AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE 'src/test/java/org/apache/commons/lang3%'
        ), tested_functions AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE 'src/main/java/org/apache/commons/lang3%'
        ), co_changed_weeks AS (
            SELECT change_week FROM changes_week_based WHERE target_method_id IN test_methods
            INTERSECT
            SELECT change_week FROM changes_week_based WHERE target_method_id IN tested_functions
        )
        SELECT change_week, change_type, COUNT(*) FROM changes_week_based
        WHERE change_week IN co_changed_weeks AND target_method_id IN test_methods
        GROUP BY change_week, change_type
    """
