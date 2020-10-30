from datetime import datetime
from sqlite3 import Connection
from commits2sql.database.table_handler import AbsSqlStmtHolder, AbsTableHandler


class CommitStmtHolder(AbsSqlStmtHolder):
    def create_db_stmt(self) -> str:
        return """
        CREATE TABLE if NOT EXISTS git_commits(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            hash_value VARCHAR(63) NOT NULL, 
            commit_date DATE NOT NULL,
            CONSTRAINT hash_unique UNIQUE (hash_value)
        )
        """

    def insert_row_stmt(self) -> str:
        return """
        INSERT INTO git_commits (hash_value, commit_date)
            VALUES (:commit_hash, :commit_date) 
        """

    def count_commit_stmts(self) -> str:
        return """
        SELECT COUNT(*) FROM git_commits 
            WHERE hash_value = :commit_hash
        """

    def select_primary_key_stmt(self) -> str:
        # SHOULD NOT BE USED
        return """
        SELECT hash_value FROM git_commits
            WHERE hash_value = :commit_hash
        """


class CommitTableHandler(AbsTableHandler):

    __DATE_TO_STR_FORMAT = "%Y-%m-%d"

    def __init__(self, db_connection: Connection):
        AbsTableHandler.__init__(self, db_connection, CommitStmtHolder())
        self.__commit_hash = None
        self.__commit_date = None

    def is_hash_exist(self, commit_hash: str):
        count_sql = self._get_stmts_holder().count_commit_stmts()
        res_cursor = self._get_db_connection().execute(
            count_sql, {"commit_hash": commit_hash}
        )
        is_recorded_before = res_cursor.fetchone()[0] != 0
        res_cursor.close()
        return is_recorded_before

    def insert_new_commit(self, commit_hash: str, commit_date: datetime):
        return self._insert_new_row(
            commit_hash=commit_hash,
            commit_date=commit_date.strftime(CommitTableHandler.__DATE_TO_STR_FORMAT),
        )

    def _get_stmts_holder(self) -> CommitStmtHolder:
        stmts = super(CommitTableHandler, self)._get_stmts_holder()
        if not isinstance(stmts, CommitStmtHolder):
            raise TypeError("IMPOSSIBLE")
        return stmts
