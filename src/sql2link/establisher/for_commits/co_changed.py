from sql2link.establisher import AbsLinkEstablisher


class CoChangedInCommitLinkEstablisher(AbsLinkEstablisher):

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str: return '''
        DROP TABLE IF EXISTS links_commits_based_cochanged
    '''

    @property
    def _initial_table_sql(self) -> str: return '''
        CREATE TABLE links_commits_based_cochanged (
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
        INSERT INTO links_commits_based_cochanged (
            tested_method_id, 
            test_method_id, 
            support_num, 
            confidence_num
        )  VALUES(?, ?, ?, ?)
        '''

    @property
    def _link_establishing_sql(self) -> str: return '''
        WITH valid_methods AS (
            SELECT id, file_path FROM git_methods
            WHERE simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ), tested_methods AS (
            SELECT valid_methods.id AS tested_method_id, commit_hash FROM (
                git_changes  INNER JOIN valid_methods
                ON valid_methods.id = git_changes.target_method_id
            )
            WHERE file_path LIKE :tested_path
        ), test_methods AS (
            SELECT valid_methods.id AS test_method_id, commit_hash FROM (
                git_changes INNER JOIN valid_methods
                ON valid_methods.id = git_changes.target_method_id
            )
            WHERE valid_methods.file_path LIKE :test_path
        ), tested_change_count AS (
            SELECT tested_method_id AS count_id, COUNT(tested_method_id) AS change_num FROM tested_methods
            GROUP BY tested_method_id
        ), co_change_table AS (
            SELECT tested_method_id, test_method_id, COUNT(*) AS support 
            FROM tested_methods INNER JOIN test_methods
                ON test_methods.commit_hash = tested_methods.commit_hash
            GROUP BY tested_method_id, test_method_id
        ), most_frequent_co_changes AS (
            SELECT tested_method_id, test_method_id, support 
            FROM co_change_table
            GROUP BY test_method_id
                HAVING MAX(support)
        )
        SELECT 
            tested_method_id, 
            test_method_id, 
            support, 
            CAST(support AS FLOAT)/change_num AS confidence 
        FROM most_frequent_co_changes 
        INNER JOIN tested_change_count
            ON tested_method_id = count_id
    '''


class CoChangedInCommitClassLevelLinkEstablisher(AbsLinkEstablisher):

    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str: return '''
        DROP TABLE IF EXISTS links_commits_based_cochanged_classes
    '''

    @property
    def _initial_table_sql(self) -> str: return '''
        CREATE TABLE links_commits_based_cochanged_classes ( 
            tested_class VARCHAR (64) NOT NULL, 
            tested_file VARCHAR (64) NOT NULL, 
            test_class VARCHAR (64) NOT NULL, 
            test_file VARCHAR (64) NOT NULL, 
            support_num INTEGER NOT NULL,
            confidence_num FLOAT NOT NULL
        );
    '''

    @property
    def _insert_new_row_sql(self) -> str:
        return '''
        INSERT INTO links_commits_based_cochanged_classes (
            tested_class, 
            tested_file, 
            test_class,
            test_file,
            support_num, 
            confidence_num
        )  VALUES(?, ?, ?, ?, ?, ?)
        '''

    @property
    def _link_establishing_sql(self) -> str: return '''
        WITH valid_methods AS (
            SELECT id, class_name, file_path FROM git_methods
            WHERE simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ), tested_functions AS (
            SELECT id AS tested_id, class_name, file_path FROM valid_methods 
            WHERE file_path LIKE :tested_path        
        ), test_methods AS (
            SELECT id AS test_id, class_name, file_path FROM valid_methods 
            WHERE file_path LIKE :test_path        
        ), tested_classes_changes AS (
            SELECT DISTINCT 
                class_name AS tested_class, 
                file_path AS tested_file, 
                commit_hash
            FROM git_changes
            INNER JOIN tested_functions
            ON target_method_id = tested_id
        ), test_classes_changes AS (
            SELECT DISTINCT 
                class_name AS test_class, 
                file_path AS test_file, 
                commit_hash
            FROM git_changes
            INNER JOIN test_methods
            ON target_method_id = test_id
        ), tested_classes_changes_count AS (
            SELECT 
                tested_class AS count_class, 
                tested_file AS count_file, 
                COUNT(*) AS change_num 
            FROM tested_classes_changes
            GROUP BY tested_class, tested_file
        ), co_change_table AS (
            SELECT 
                tested_class, tested_file,
                test_class, test_file, 
                COUNT(*) AS support
            FROM test_classes_changes
            INNER JOIN tested_classes_changes
            ON test_classes_changes.commit_hash = tested_classes_changes.commit_hash
            GROUP BY tested_class, tested_file, test_class, test_file
        )
        SELECT
            tested_class, tested_file,
            test_class, test_file,
            support, CAST(support AS FLOAT)/change_num AS confidence
        FROM  co_change_table
        INNER JOIN tested_classes_changes_count
        ON tested_class = count_class
        AND tested_file = count_file
        
    '''
