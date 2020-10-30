from sql2link.establisher.abs_link_builder import AbsLinkEstablisher


class AprioriInWeekLinkEstablisher(AbsLinkEstablisher):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return """
        DROP TABLE IF EXISTS links_weeks_based_apriori
    """

    @property
    def _initial_table_sql(self) -> str:
        return """
        CREATE TABLE links_weeks_based_apriori (
            tested_method_id INTEGER NOT NULL,
            test_method_id INTEGER NOT NULL,
            support_num INTEGER NOT NULL,
            confidence_num FLOAT NOT NULL,
            FOREIGN KEY (tested_method_id) REFERENCES git_methods(id), 
            FOREIGN KEY (test_method_id) REFERENCES git_methods(id)
        );
    """

    @property
    def _insert_new_row_sql(self) -> str:
        return """
        INSERT INTO links_weeks_based_apriori (
            tested_method_id, 
            test_method_id, 
            support_num, 
            confidence_num
        ) VALUES(?, ?, ?, ?)
    """

    @property
    def _link_establishing_sql(self) -> str:
        return """
        WITH week_commit_table AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash  FROM git_commits
        ),
        alive_methods AS (
            SELECT id, file_path FROM git_methods
            WHERE NOT EXISTS(
                SELECT target_method_id FROM git_changes
                WHERE change_type = 'REMOVE' AND target_method_id = id
            )
            AND simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ),
        week_based_changes AS (
            SELECT target_method_id, week AS change_week, file_path FROM (
                git_changes JOIN week_commit_table JOIN alive_methods
                ON git_changes.commit_hash = week_commit_table.commit_hash
                AND git_changes.target_method_id = alive_methods.id
            )
            GROUP BY target_method_id, change_week
        ),
        tested_modified AS (
            SELECT target_method_id AS tested_method_id, change_week FROM week_based_changes
            WHERE file_path LIKE :tested_path
        ),
        test_modified AS (
            SELECT target_method_id AS test_method_id, change_week FROM week_based_changes
            WHERE file_path LIKE :test_path
        ),
        frequent_tested AS (
            SELECT tested_method_id, COUNT(*) AS support FROM tested_modified
            GROUP BY tested_method_id HAVING support > :min_support_for_change
        ),
        frequent_test AS (
            SELECT test_method_id, COUNT(*) AS support FROM test_modified
            GROUP BY test_method_id
        ),
        co_changed AS (
            SELECT tested_method_id, test_method_id, COUNT(*) AS support FROM (
                tested_modified INNER JOIN test_modified
                ON test_modified.change_week = tested_modified.change_week
                AND EXISTS(
                    SELECT test_method_id FROM frequent_test
                    WHERE frequent_test.test_method_id = test_method_id
                )
                AND EXISTS(
                    SELECT tested_method_id FROM frequent_tested
                    WHERE frequent_tested.tested_method_id = tested_method_id
                )
            )
            GROUP BY tested_method_id, test_method_id HAVING support > :min_support_for_cochange
        )
        SELECT co_changed.tested_method_id,
               co_changed.test_method_id,
               co_changed.support,
               CAST(co_changed.support AS FLOAT)/frequent_tested.support AS confidence
        FROM (
            co_changed INNER JOIN frequent_tested
            ON co_changed.tested_method_id = frequent_tested.tested_method_id
        ) WHERE confidence > :min_confidence;
    """
