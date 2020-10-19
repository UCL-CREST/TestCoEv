from sql2link.establisher import AbsLinkEstablisher


class AprioriInCommitLinkEstablisher(AbsLinkEstablisher):

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return '''
        DROP TABLE IF EXISTS links_commits_based_apriori
        '''

    @property
    def _initial_table_sql(self) -> str:
        return '''
        CREATE TABLE links_commits_based_apriori (
            tested_method_id INTEGER NOT NULL,
            test_method_id INTEGER NOT NULL,
            support_num INTEGER NOT NULL,
            confidence_num FLOAT NOT NULL,
            FOREIGN KEY (tested_method_id) REFERENCES git_methods(id), 
            FOREIGN KEY (test_method_id) REFERENCES git_methods(id)
        );
        '''

    @property
    def _insert_new_row_sql(self) -> str:
        return '''
        INSERT INTO links_commits_based_apriori (
            tested_method_id, 
            test_method_id, 
            support_num, 
            confidence_num
        ) VALUES(?, ?, ?, ?)
        '''

    @property
    def _link_establishing_sql(self) -> str: return '''
        WITH valid_methods AS (
            SELECT id, file_path FROM git_methods
            WHERE simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ), 
        test_methods AS (
            SELECT id FROM valid_methods
            WHERE file_path LIKE :test_path
        ),
        tested_functions AS (
            SELECT id FROM valid_methods
            WHERE file_path LIKE :tested_path
        ), 
        frequent_method AS (
            SELECT 
                target_method_id AS test_id, 
                COUNT(*) AS test_support 
            FROM git_changes
            WHERE test_id IN test_methods
            GROUP BY test_id
                HAVING test_support >= :min_test_changes_support
        ),
        frequent_functions AS (
            SELECT 
                target_method_id AS tested_id, 
                COUNT(*) AS tested_support 
            FROM git_changes
            WHERE tested_id IN tested_functions
            GROUP BY tested_id
                HAVING tested_support >= :min_tested_changes_support
        ),
        frequent_methods_changes AS (
            SELECT commit_hash, test_id, test_support
            FROM frequent_method 
            INNER JOIN git_changes
                ON target_method_id = test_id
        ),
        frequent_functions_changes AS (
            SELECT commit_hash, tested_id, tested_support
            FROM frequent_functions
            INNER JOIN git_changes
                ON target_method_id = tested_id
        ),
        frequent_cochange_table AS(
            SELECT 
                tested_id, test_id, 
                COUNT(*) AS cochange_support, 
                tested_support 
            FROM frequent_methods_changes 
            INNER JOIN frequent_functions_changes
                ON frequent_methods_changes.commit_hash = frequent_functions_changes.commit_hash
            GROUP BY tested_id, test_id
                HAVING cochange_support >= :min_coevolved_changes_support
        )
        SELECT 
            tested_id, 
            test_id, 
            cochange_support, 
            MAX(CAST(cochange_support AS FLOAT)/tested_support ) AS confidence 
        FROM frequent_cochange_table
        GROUP BY test_id HAVING confidence >= :min_confidence
        '''
