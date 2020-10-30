from sql2link.establisher import AbsLinkEstablisher


class CoChangedtedForSeparateChangeTypeFilteredCommitLinkEstablisher(
    AbsLinkEstablisher
):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return """
        DROP TABLE IF EXISTS links_filtered_commits_based_cochanged
    """

    @property
    def _initial_table_sql(self) -> str:
        return """
        CREATE TABLE links_filtered_commits_based_cochanged (
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
        INSERT INTO links_filtered_commits_based_cochanged (
            tested_method_id, test_method_id, support, confidence_num
        ) VALUES(?, ?, ?, ?)
    """

    @property
    def _link_establishing_sql(self) -> str:
        return """
        WITH commits_changes_count AS (
            SELECT
                commit_hash,
                COUNT(CASE WHEN change_type = 'ADD' THEN 1 END) AS add_count,
                COUNT(CASE WHEN change_type = 'MODIFY' THEN 1 END) AS modify_count,
                COUNT(CASE WHEN change_type = 'RENAME' THEN 1 END) AS rename_count
            FROM git_changes
            GROUP BY
                commit_hash
        ), 
        valid_commits AS (
            SELECT DISTINCT commit_hash
            FROM commits_changes_count
            WHERE add_count BETWEEN :add_min AND :add_max
                AND modify_count BETWEEN :modify_min AND :modify_max
                AND rename_count BETWEEN :rename_min AND :rename_max
        ),  filtered_change AS (
            SELECT * FROM git_changes
            WHERE commit_hash IN valid_commits
        ), valid_methods AS (
            SELECT id, file_path FROM git_methods
            WHERE simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ), tested_functions AS (
            SELECT valid_methods.id AS tested_method_id, commit_hash
            FROM filtered_change
            INNER JOIN valid_methods
                ON valid_methods.id = filtered_change.target_method_id
            WHERE file_path LIKE :tested_path
        ), test_methods AS (
            SELECT valid_methods.id AS test_method_id, commit_hash
            FROM filtered_change
            INNER JOIN valid_methods
                ON valid_methods.id = filtered_change.target_method_id
            WHERE valid_methods.file_path LIKE :test_path
        ), test_change_count AS (
            SELECT test_method_id AS count_id, COUNT(*) AS change_num
            FROM test_methods
            GROUP BY test_method_id
        ), co_change_table AS (
            SELECT tested_method_id, test_method_id, COUNT(*) AS support
            FROM tested_functions
            INNER JOIN test_methods
                ON test_methods.commit_hash = tested_functions.commit_hash
            GROUP BY tested_method_id, test_method_id
        )
        SELECT
               tested_method_id,
               test_method_id,
               MAX(support),
               CAST(support AS FLOAT)/change_num AS confidence
        FROM co_change_table
            INNER JOIN test_change_count
        GROUP BY test_method_id
        
    """


class CoChangedtedForAllChangeTypeFilteredCommitLinkEstablisher(AbsLinkEstablisher):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return """
        DROP TABLE IF EXISTS links_filtered_commits_based_cochanged
    """

    @property
    def _initial_table_sql(self) -> str:
        return """
        CREATE TABLE links_filtered_commits_based_cochanged (
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
        INSERT INTO links_filtered_commits_based_cochanged (
            tested_method_id, test_method_id, support, confidence_num
        ) VALUES(?, ?, ?, ?)
    """

    @property
    def _link_establishing_sql(self) -> str:
        return """
        WITH valid_commits AS (
            SELECT DISTINCT commit_hash 
            FROM git_changes
            GROUP BY commit_hash 
                HAVING COUNT(*) BETWEEN :changes_count_min AND :changes_count_max
        ), filtered_change AS (
            SELECT * FROM git_changes
            WHERE commit_hash IN valid_commits
        ), valid_methods AS (
            SELECT id, file_path FROM git_methods
            WHERE simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ), tested_functions AS (
            SELECT valid_methods.id AS tested_method_id, commit_hash 
            FROM filtered_change 
            INNER JOIN valid_methods
                ON valid_methods.id = filtered_change.target_method_id
            WHERE file_path LIKE :tested_path
        ), test_methods AS (
            SELECT valid_methods.id AS test_method_id, commit_hash
            FROM filtered_change 
            INNER JOIN valid_methods
                ON valid_methods.id = filtered_change.target_method_id
            WHERE valid_methods.file_path LIKE :test_path
        ), test_change_count AS (
            SELECT test_method_id AS count_id, COUNT(*) AS change_num 
            FROM test_methods
            GROUP BY test_method_id
        ), co_change_table AS (
            SELECT tested_method_id, test_method_id, COUNT(*) AS support 
            FROM tested_functions 
            INNER JOIN test_methods
                ON test_methods.commit_hash = tested_functions.commit_hash
            GROUP BY tested_method_id, test_method_id
        )
        SELECT 
            tested_method_id, 
            test_method_id, 
            MAX(support), 
            CAST(support AS FLOAT)/change_num AS confidence 
        FROM co_change_table 
        INNER JOIN test_change_count
            ON test_method_id = count_id
        GROUP BY test_method_id
        
        
    """


class CoCreatedWithFilteredCommitLinkEstablisher(AbsLinkEstablisher):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return """
        DROP TABLE IF EXISTS links_filtered_commits_based_cocreated
    """

    @property
    def _initial_table_sql(self) -> str:
        return """
        CREATE TABLE links_filtered_commits_based_cocreated (
            tested_method_id INTEGER NOT NULL,
            test_method_id INTEGER NOT NULL,
            confidence_num INTEGER NOT NULL,
            FOREIGN KEY (tested_method_id) REFERENCES git_methods(id), 
            FOREIGN KEY (test_method_id) REFERENCES git_methods(id)
        );
    """

    @property
    def _insert_new_row_sql(self) -> str:
        return """
        INSERT INTO links_filtered_commits_based_cocreated (
            tested_method_id, test_method_id, confidence_num
        ) VALUES(?, ?, 1)
    """

    @property
    def _link_establishing_sql(self) -> str:
        return """
        WITH valid_commits AS (
            SELECT commit_hash 
            FROM git_changes
                WHERE change_type = 'ADD' 
            GROUP BY commit_hash 
            HAVING COUNT(*) > :add_min AND COUNT(*) < :add_max
        ), filtered_change AS (
            SELECT * FROM git_changes
            WHERE commit_hash IN valid_commits
        ), valid_methods AS (
            SELECT id, file_path FROM git_methods
            WHERE simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ), tested_functions AS (
            SELECT valid_methods.id AS tested_method_id, commit_hash FROM (
                filtered_change INNER JOIN valid_methods
                ON valid_methods.id = filtered_change.target_method_id
            )
            WHERE file_path LIKE :tested_path
        ), test_methods AS (
            SELECT valid_methods.id AS test_method_id, commit_hash FROM (
                filtered_change INNER JOIN valid_methods
                ON valid_methods.id = filtered_change.target_method_id
            )
            WHERE valid_methods.file_path LIKE :test_path
        )
        SELECT tested_method_id, test_method_id FROM (
            tested_functions INNER JOIN test_methods
            ON tested_functions.commit_hash = test_methods.commit_hash
        )
    """


class AprioriWithFilteredCommitLinkEstablisher(AbsLinkEstablisher):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return """
        DROP TABLE IF EXISTS links_filtered_commits_based_apriori
    """

    @property
    def _initial_table_sql(self) -> str:
        return """
        CREATE TABLE links_filtered_commits_based_apriori (
            tested_method_id INTEGER NOT NULL,
            test_method_id INTEGER NOT NULL,
            support_num INTEGER NOT NULL, 
            confidence_num INTEGER NOT NULL,
            FOREIGN KEY (tested_method_id) REFERENCES git_methods(id), 
            FOREIGN KEY (test_method_id) REFERENCES git_methods(id)
        );
    """

    @property
    def _insert_new_row_sql(self) -> str:
        return """
        INSERT INTO links_filtered_commits_based_apriori (
            tested_method_id, test_method_id, support_num, confidence_num
        ) VALUES(?, ?, ?, ?)
    """

    @property
    def _link_establishing_sql(self) -> str:
        return """
        WITH valid_commits AS (
            SELECT DISTINCT commit_hash 
            FROM git_changes
            GROUP BY commit_hash 
                HAVING COUNT(*) BETWEEN :change_min AND :change_max
        ), filtered_change AS (
            SELECT * FROM git_changes
            WHERE commit_hash IN valid_commits
        ), valid_methods AS (
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
            FROM filtered_change
            WHERE test_id IN test_methods
            GROUP BY test_id
                HAVING test_support >= :min_test_changes_support
        ),
        frequent_functions AS (
            SELECT 
                target_method_id AS tested_id, 
                COUNT(*) AS tested_support 
            FROM filtered_change
            WHERE tested_id IN tested_functions
            GROUP BY tested_id
                HAVING tested_support >= :min_tested_changes_support
        ),
        frequent_methods_changes AS (
            SELECT commit_hash, test_id, test_support
            FROM frequent_method 
            INNER JOIN filtered_change
                ON target_method_id = test_id
        ),
        frequent_functions_changes AS (
            SELECT commit_hash, tested_id, tested_support
            FROM frequent_functions
            INNER JOIN filtered_change
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
            tested_id, test_id, 
            cochange_support, 
            CAST(cochange_support AS FLOAT)/tested_support AS confidence
        FROM frequent_cochange_table
        WHERE confidence >= :min_confidence
    """


class CoChangedInCommitClassLevelLinkEstablisherWithFilter(AbsLinkEstablisher):
    def __init__(self, db_path: str):
        super().__init__(db_path)

    @property
    def _remove_previous_table_sql(self) -> str:
        return """
        DROP TABLE IF EXISTS links_filtered_commits_based_cochanged_classes
    """

    @property
    def _initial_table_sql(self) -> str:
        return """
        CREATE TABLE links_filtered_commits_based_cochanged_classes ( 
            tested_class VARCHAR (64) NOT NULL, 
            tested_file VARCHAR (64) NOT NULL, 
            test_class VARCHAR (64) NOT NULL, 
            test_file VARCHAR (64) NOT NULL, 
            support_num INTEGER NOT NULL,
            confidence_num FLOAT NOT NULL
        );
    """

    @property
    def _insert_new_row_sql(self) -> str:
        return """
        INSERT INTO links_filtered_commits_based_cochanged_classes (
            tested_class, 
            tested_file, 
            test_class,
            test_file,
            support_num, 
            confidence_num
        )  VALUES(?, ?, ?, ?, ?, ?)
        """

    @property
    def _link_establishing_sql(self) -> str:
        return """
        WITH valid_methods AS (
            SELECT id, class_name, file_path FROM git_methods
            WHERE simple_name NOT IN ('main(String [ ] args)', 'suite()', 'setUp()', 'tearDown()')
            AND simple_name NOT LIKE ('for(int i%')
        ), class_changes AS (
            SELECT class_name, file_path, commit_hash
            FROM git_changes
            INNER JOIN valid_methods
            ON valid_methods.id = target_method_id
        ), valid_commits AS (
            SELECT commit_hash
            FROM class_changes
            GROUP BY commit_hash
            HAVING COUNT(*) > :changes_count_min
                AND  COUNT(*) < :changes_count_max
        ), tested_classes AS (
            SELECT DISTINCT
                class_name AS tested_class,
                file_path AS tested_file
            FROM valid_methods
            WHERE tested_file LIKE :tested_path
        ), test_classes AS (
            SELECT DISTINCT
                class_name AS test_class,
                file_path AS test_file
            FROM valid_methods
            WHERE test_file LIKE :test_path
        ), tested_classes_changes AS (
            SELECT DISTINCT tested_class, tested_file, commit_hash
            FROM class_changes
                INNER JOIN tested_classes
            ON class_name = tested_class
                AND file_path = tested_file
            WHERE commit_hash IN valid_commits
        ), test_classes_changes AS (
            SELECT DISTINCT test_class, test_file, commit_hash
            FROM class_changes
                INNER JOIN test_classes
            ON class_name = test_class
                AND file_path = test_file
            WHERE commit_hash IN valid_commits
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
    """
