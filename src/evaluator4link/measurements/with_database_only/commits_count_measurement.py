import abc
from typing import Dict, List, Tuple
from evaluator4link.measurements import AbstractMeasurement


class AbstractCommitsCountMeasurement(AbstractMeasurement):
    __metaclass__ = abc.ABCMeta

    @property
    @abc.abstractmethod
    def _count_changes_in_commit_sql_stmt(self) -> str:
        pass

    @property
    def commits_xs_mapping(self) -> Dict[str, int]:
        return self.__commit_xs_table

    @property
    def type_zs_mapping(self) -> Dict[str, int]:
        return self.__type_zs_table

    @property
    def commits_count_coordinates(self) -> List[Tuple[int, int, int]]:
        return self.__commit_change_counts

    def __init__(
        self,
        path_to_db: str,
        path_to_test: str = "src/test%",
        path_to_tested: str = "src/main%",
    ):
        self.__commit_xs_table: Dict[str, int] = dict()
        self.__type_zs_table: Dict[str, int] = {
            "ADD": 1,
            "MODIFY": 2,
            "RENAME": 3,
            "REMOVE": 4,
        }
        self.__commit_change_counts: List[Tuple[int, int, int]] = list()
        self.__paths = {"test_path": path_to_test, "tested_path": path_to_tested}
        super().__init__(path_to_db)

    def _measure(self) -> None:
        cursor = self._predict_database.cursor()
        exe_res = cursor.execute(self._count_changes_in_commit_sql_stmt, self.__paths)
        for commit_hash, change_type, change_count in exe_res:
            x_val = self.__from_hash_to_x_value(commit_hash)
            y_val = change_count
            z_val = self.__from_change_type_to_y_value(change_type)
            self.__commit_change_counts.append((x_val, y_val, z_val))
        cursor.close()
        return None

    def __from_hash_to_x_value(self, hash_value: str) -> int:
        if hash_value not in self.__commit_xs_table:
            self.__commit_xs_table[hash_value] = len(self.__commit_xs_table) + 1
        return self.__commit_xs_table[hash_value]

    def __from_change_type_to_y_value(self, change_type: str) -> int:
        return self.__type_zs_table[change_type]


class FileCommitsCountMeasurement(AbstractCommitsCountMeasurement):
    @property
    def _count_changes_in_commit_sql_stmt(self) -> str:
        return """
        WITH files_changes AS (
            SELECT DISTINCT commit_hash, change_type, file_path FROM (
                git_changes INNER JOIN git_methods
                ON git_changes.target_method_id =  git_methods.id
            )
        ), test_files AS (
            SELECT DISTINCT file_path FROM git_methods
            WHERE file_path LIKE :test_path
        ), tested_files AS (
            SELECT DISTINCT file_path FROM git_methods
            WHERE file_path LIKE :tested_path
        ), co_changed_commits AS (
            SELECT commit_hash FROM files_changes WHERE file_path IN test_files
            INTERSECT
            SELECT commit_hash FROM files_changes WHERE file_path IN tested_files
        )
        SELECT commit_hash, change_type, COUNT(*) FROM files_changes
        WHERE commit_hash IN co_changed_commits
        GROUP BY commit_hash, change_type
    """


class ClassCommitsCountMeasurement(AbstractCommitsCountMeasurement):
    @property
    def _count_changes_in_commit_sql_stmt(self) -> str:
        return """
        WITH classes_changes AS (
            SELECT DISTINCT commit_hash, change_type, (class_name || file_path) AS unique_class_id FROM (
                git_changes INNER JOIN git_methods
                ON git_changes.target_method_id =  git_methods.id
            )
        ), test_classes AS (
            SELECT DISTINCT (class_name || file_path) AS unique_class_id FROM git_methods
            WHERE file_path LIKE :test_path
        ), tested_classes AS (
            SELECT DISTINCT (class_name || file_path) AS unique_class_id FROM git_methods
            WHERE file_path LIKE :tested_path
        ), co_changed_commits AS (
            SELECT commit_hash FROM classes_changes WHERE unique_class_id IN test_classes
            INTERSECT
            SELECT commit_hash FROM classes_changes WHERE unique_class_id IN tested_classes
        )
        SELECT commit_hash, change_type, COUNT(*) FROM classes_changes
        WHERE commit_hash IN co_changed_commits
        GROUP BY commit_hash, change_type
    """


class MethodCommitsCountMeasurement(AbstractCommitsCountMeasurement):
    @property
    def _count_changes_in_commit_sql_stmt(self) -> str:
        return """
        WITH test_methods AS (
            SELECT DISTINCT id FROM git_methods WHERE file_path LIKE :test_path
        ), tested_functions AS (
            SELECT DISTINCT id FROM git_methods WHERE file_path LIKE :tested_path
        ), co_changed_commits AS (
            SELECT commit_hash FROM git_changes WHERE target_method_id IN test_methods
            INTERSECT
            SELECT commit_hash FROM git_changes WHERE target_method_id IN tested_functions
        )
        SELECT commit_hash, change_type, COUNT(*) FROM git_changes
        WHERE commit_hash IN co_changed_commits
        GROUP BY commit_hash, change_type
    """


class TestedCommitsCountMeasurement(AbstractCommitsCountMeasurement):
    @property
    def _count_changes_in_commit_sql_stmt(self) -> str:
        return """
        WITH test_methods AS (
            SELECT DISTINCT id FROM git_methods WHERE file_path LIKE :test_path
        ), tested_functions AS (
            SELECT DISTINCT id FROM git_methods WHERE file_path LIKE :tested_path
        ), co_changed_commits AS (
            SELECT commit_hash FROM git_changes WHERE target_method_id IN test_methods
            INTERSECT
            SELECT commit_hash FROM git_changes WHERE target_method_id IN tested_functions
        )
        SELECT commit_hash, change_type, COUNT(*) FROM git_changes
        WHERE commit_hash IN co_changed_commits 
        AND target_method_id IN tested_functions
        GROUP BY commit_hash, change_type 
    """


class TestCommitsCountMeasurement(AbstractCommitsCountMeasurement):
    @property
    def _count_changes_in_commit_sql_stmt(self) -> str:
        return """
        WITH test_methods AS (
            SELECT DISTINCT id FROM git_methods WHERE file_path LIKE :test_path
        ), tested_functions AS (
            SELECT DISTINCT id FROM git_methods WHERE file_path LIKE :tested_path
        ), co_changed_commits AS (
            SELECT commit_hash FROM git_changes WHERE target_method_id IN test_methods
            INTERSECT
            SELECT commit_hash FROM git_changes WHERE target_method_id IN tested_functions
        )
        SELECT commit_hash, change_type, COUNT(*) FROM git_changes
        WHERE commit_hash IN co_changed_commits 
        AND target_method_id IN test_methods
        GROUP BY commit_hash, change_type 
    """
