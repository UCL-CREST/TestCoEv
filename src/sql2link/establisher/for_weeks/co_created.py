from sql2link.establisher import AbsLinkEstablisher


class CoCreatedInWeekLinkEstablisher(AbsLinkEstablisher):

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return '''
        DROP TABLE IF EXISTS links_weeks_based_cocreated
        '''

    @property
    def _initial_table_sql(self) -> str:
        return '''
        CREATE TABLE links_weeks_based_cocreated (
            tested_method_id INTEGER NOT NULL,
            test_method_id INTEGER NOT NULL,
            confidence_num INTEGER, 
            FOREIGN KEY (tested_method_id) REFERENCES git_methods(id), 
            FOREIGN KEY (test_method_id) REFERENCES git_methods(id)
        );
        '''

    @property
    def _insert_new_row_sql(self) -> str:
        return '''
        INSERT INTO links_weeks_based_cocreated (tested_method_id, test_method_id, confidence_num) VALUES(?, ?, 1)
        '''

    @property
    def _link_establishing_sql(self) -> str:
        return '''
        WITH week_commit_table AS (
            SELECT STRFTIME('%Y-%W', commit_date)  AS week, hash_value AS commit_hash FROM git_commits
        ),
        alive_methods AS (
            SELECT id, file_path FROM git_methods
            WHERE NOT EXISTS(
                SELECT target_method_id FROM git_changes
                WHERE change_type = 'REMOVE' AND target_method_id = id
            )
            AND simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE (class_name || '%') AND simple_name NOT LIKE ('for(int i%')
        ),
        added_week_table AS (
            SELECT target_method_id, week AS change_week FROM (
                git_changes JOIN week_commit_table JOIN alive_methods
                ON git_changes.commit_hash = week_commit_table.commit_hash
                AND target_method_id = alive_methods.id
                AND change_type = 'ADD'
            )
            GROUP BY target_method_id, change_week
        ),
        tested_added AS (
            SELECT id AS tested_method_id, change_week FROM (
                added_week_table INNER JOIN alive_methods 
                ON id = target_method_id
            )
            WHERE file_path LIKE :tested_path
        ),
        test_added AS (
            SELECT id AS test_method_id, change_week FROM (                
                added_week_table INNER JOIN alive_methods 
                ON id = target_method_id
            ) 
            WHERE file_path LIKE :test_path
        )
        SELECT DISTINCT tested_method_id, test_method_id FROM (
            tested_added INNER JOIN test_added
            ON tested_added.change_week = test_added.change_week
        ) 
        '''
