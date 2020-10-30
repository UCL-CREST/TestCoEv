import abc
from abc import ABC, ABCMeta

from sql2link.establisher import AbsLinkEstablisher


class AbstractCoChangedWithFilterWeekLinkEstablisher(
    AbsLinkEstablisher, metaclass=ABCMeta
):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return """
        DROP TABLE IF EXISTS links_filtered_weeks_based_cochanged
    """

    @property
    def _initial_table_sql(self) -> str:
        return """
        CREATE TABLE links_filtered_weeks_based_cochanged (
            tested_method_id INTEGER NOT NULL,
            test_method_id INTEGER NOT NULL,
            support INTEGER NOT NULL, 
            confidence_num INTEGER,
            FOREIGN KEY (tested_method_id) REFERENCES git_methods(id), 
            FOREIGN KEY (test_method_id) REFERENCES git_methods(id)
        );
    """

    @property
    def _insert_new_row_sql(self) -> str:
        return """
        INSERT INTO links_filtered_weeks_based_cochanged (
            tested_method_id, test_method_id, support, confidence_num
        ) VALUES(?, ?, ?, ?)
    """


class CoChangedtedForSeparateChangeTypeFilteredWeekLinkEstablisher(
    AbstractCoChangedWithFilterWeekLinkEstablisher
):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _link_establishing_sql(self) -> str:
        return """
        WITH commits_to_weeks AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash FROM git_commits
        ),
        changes_week_based AS (
            SELECT DISTINCT target_method_id, change_type, week AS change_week FROM (
                git_changes INNER JOIN commits_to_weeks
                ON git_changes.commit_hash = commits_to_weeks.commit_hash
            )
        ),
        weeks_changes_count AS (
            SELECT change_week, change_type, COUNT(*) AS change_count FROM changes_week_based
            GROUP BY change_week, change_type
        ),
        invalid_weeks AS (
            SELECT DISTINCT change_week FROM weeks_changes_count
            WHERE (change_type == 'ADD' AND change_count > :add_count_limits)
            OR (change_type == 'MODIFY' AND change_count > :modify_count_limits)
            OR (change_type == 'RENAME' AND change_count > :rename_count_limits)
        ),
        filtered_change AS (
            SELECT * FROM changes_week_based
            WHERE change_week NOT IN invalid_weeks
        ),
        tested_functions AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE :tested_path
        ),
        tested_changes AS (
            SELECT target_method_id AS tested_id, change_week FROM filtered_change
            WHERE target_method_id IN tested_functions
        ),
        test_methods AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE :test_path
        ),
        test_changes AS (
            SELECT target_method_id AS test_id, change_week FROM filtered_change
            WHERE target_method_id IN test_methods
        ),
        tested_change_count AS (
            SELECT target_method_id AS count_id, COUNT(*) AS change_num FROM filtered_change
            WHERE target_method_id IN tested_functions
            GROUP BY target_method_id
        ),
        co_change_table AS (
            SELECT tested_id, test_id, COUNT(*) AS support FROM (
                test_changes INNER JOIN tested_changes
                ON test_changes.change_week = tested_changes.change_week
            )
            GROUP BY tested_id, test_id
        )
        SELECT 
            tested_id, 
            test_id, 
            support, 
            CAST(support AS FLOAT)/change_num AS confidence 
        FROM co_change_table 
            INNER JOIN tested_change_count
            ON tested_id = count_id
        
    """


class CoChangedtedForAllChangeTypeFilteredWeekLinkEstablisher(
    AbstractCoChangedWithFilterWeekLinkEstablisher
):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _link_establishing_sql(self) -> str:
        return """
        WITH commits_to_weeks AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash FROM git_commits
        ),
        changes_week_based AS (
            SELECT DISTINCT target_method_id, change_type, week AS change_week FROM (
                git_changes INNER JOIN commits_to_weeks
                ON git_changes.commit_hash = commits_to_weeks.commit_hash
            )
        ),
        weeks_changes_count AS (
            SELECT change_week, change_type, COUNT(*) AS change_count FROM changes_week_based
            GROUP BY change_week, change_type
        ),
        invalid_weeks AS (
            SELECT change_week FROM weeks_changes_count
            GROUP BY change_week 
            HAVING SUM(change_count) > :total_count_max 
            OR SUM(change_count) < :total_count_min
        ),
        filtered_change AS (
            SELECT * FROM changes_week_based
            WHERE change_week NOT IN invalid_weeks
        ),
        tested_functions AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE :tested_path
        ),
        tested_changes AS (
            SELECT target_method_id AS tested_id, change_week FROM filtered_change
            WHERE target_method_id IN tested_functions
        ),
        test_methods AS (
            SELECT id FROM git_methods
            WHERE file_path LIKE :test_path
        ),
        test_changes AS (
            SELECT target_method_id AS test_id, change_week FROM filtered_change
            WHERE target_method_id IN test_methods
        ),
        tested_change_count AS (
            SELECT target_method_id AS count_id, COUNT(*) AS change_num FROM filtered_change
            WHERE target_method_id IN tested_functions
            GROUP BY target_method_id
        ),
        co_change_table AS (
            SELECT tested_id, test_id, COUNT(*) AS support FROM (
                test_changes INNER JOIN tested_changes
                ON test_changes.change_week = tested_changes.change_week
            )
            GROUP BY tested_id, test_id
        )
        SELECT tested_id, test_id, support, CAST(support AS FLOAT)/change_num AS confidence FROM (
            co_change_table INNER JOIN tested_change_count
            ON tested_id = count_id
        )
    """
