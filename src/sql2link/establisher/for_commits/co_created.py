from sql2link.establisher import AbsLinkEstablisher


class CoCreatedInCommitLinkEstablisher(AbsLinkEstablisher):

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return '''
        DROP TABLE IF EXISTS links_commits_based_cocreated
        '''

    @property
    def _initial_table_sql(self) -> str:
        return '''
        CREATE TABLE links_commits_based_cocreated (
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
        INSERT INTO links_commits_based_cocreated (tested_method_id, test_method_id, confidence_num) VALUES(?, ?, 1)
        '''

    @property
    def _link_establishing_sql(self) -> str:
        return '''
        WITH alive_methods AS (
            SELECT id, file_path FROM main.git_methods
            WHERE NOT EXISTS(
                SELECT target_method_id FROM git_changes
                WHERE change_type = 'REMOVE' AND target_method_id = id
            )
            AND simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ), tested_methods AS (
            SELECT alive_methods.id AS tested_method_id, commit_hash FROM alive_methods, git_changes
            WHERE file_path LIKE :tested_path
            AND change_type = 'ADD' AND alive_methods.id = git_changes.target_method_id
        ), test_methods AS (
            SELECT alive_methods.id AS test_method_id, commit_hash FROM alive_methods, git_changes
            WHERE file_path LIKE :test_path
            AND change_type = 'ADD' AND alive_methods.id = git_changes.target_method_id
        )
        SELECT tested_method_id, test_method_id FROM (
            test_methods INNER JOIN tested_methods
            ON test_methods.commit_hash = tested_methods.commit_hash
        )
        '''
