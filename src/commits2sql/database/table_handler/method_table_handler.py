from sqlite3 import Connection
from typing import List, Tuple
from commits2sql.database.table_handler import AbsSqlStmtHolder, AbsTableHandler


class MethodStmtHolder(AbsSqlStmtHolder):
    def create_db_stmt(self) -> str:
        return """
            CREATE TABLE if NOT EXISTS git_methods (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                simple_name VARCHAR(32) NOT NULL, 
                class_name VARCHAR(32) NOT NULL, 
                file_path VARCHAR(64) NOT NULL, 
                CONSTRAINT method_unique UNIQUE (simple_name, class_name, file_path)
            )
        """

    def insert_row_stmt(self) -> str:
        return """
            INSERT INTO git_methods (simple_name, class_name, file_path)
            VALUES (:method_name, :class_name, :path); 
        """

    def select_primary_key_stmt(self) -> str:
        return """
            SELECT id FROM git_methods
            WHERE simple_name = :method_name 
                AND class_name = :class_name
                AND file_path = :path
        """

    def select_crash_row_id_pair_after_relocate_stmt(self) -> str:
        return """
            SELECT OLD.id, NEW.id
            FROM (
                (SELECT id, class_name, simple_name FROM git_methods WHERE file_path = :old_path) OLD
                JOIN 
                (SELECT id, class_name, simple_name FROM git_methods WHERE file_path = :new_path) NEW
                ON OLD.class_name = NEW.class_name 
                AND OLD.simple_name = NEW.simple_name
            )
        """

    def select_crash_row_id_pair_after_rename_class_stmt(self) -> str:
        return """
            SELECT OLD.id, NEW.id
            FROM (
                (SELECT id, simple_name FROM git_methods WHERE file_path=:path AND class_name=:old_class) OLD
                JOIN 
                (SELECT id, simple_name FROM git_methods WHERE file_path=:path AND class_name=:new_class) NEW
                ON OLD.simple_name = NEW.simple_name
            )
        """

    def select_crash_row_id_pair_after_rename_method_stmt(self) -> str:
        return """
            SELECT OLD.id, NEW.id
            FROM (
                (SELECT id, file_path, class_name FROM git_methods WHERE id=:method_id) OLD
                JOIN 
                (SELECT id, file_path, class_name FROM git_methods WHERE simple_name=:new_name) NEW
                ON OLD.file_path = NEW.file_path AND OLD.class_name = NEW.class_name
            )
        """

    def delete_row_by_id_stmt(self) -> str:
        return """
            DELETE FROM git_methods 
            WHERE id = :id
        """

    def update_simple_name_stmt(self) -> str:
        return """
            UPDATE git_methods 
            SET simple_name = :new_name
            WHERE id=:method_id
        """

    def update_class_name_stmt(self) -> str:
        return """
            UPDATE git_methods 
            SET class_name = :new_class
            WHERE class_name = :old_class
                AND file_path = :path
        """

    def update_file_path_stmt(self) -> str:
        return """
            UPDATE git_methods 
            SET file_path = :new_path
            WHERE file_path = :old_path
        """


class MethodTableHandler(AbsTableHandler):
    def _get_stmts_holder(self) -> MethodStmtHolder:
        stmts = super(MethodTableHandler, self)._get_stmts_holder()
        if not isinstance(stmts, MethodStmtHolder):
            raise TypeError("IMPOSSIBLE")
        return stmts

    def __init__(self, db_connection: Connection):
        AbsTableHandler.__init__(self, db_connection, MethodStmtHolder())
        self.__commit_hash = None
        self.__commit_date = None

    def select_method_id(self, method_name: str, class_name: str, path: str):
        res_id = self._select_primary_key(
            method_name=method_name, class_name=class_name, path=path
        )
        if res_id is None:
            res_id = self._insert_new_row(
                method_name=method_name, class_name=class_name, path=path
            )
        return res_id

    def __find_crash_id_pairs(self, sql: str, **parameters) -> List[Tuple[int, int]]:
        exe_cursor = self._get_db_connection().execute(sql, parameters)
        result = [
            (each_row[0], each_row[1])
            for each_row in exe_cursor.fetchall()
            if each_row is not None and len(each_row) > 2
        ]
        exe_cursor.close()
        return result

    def find_crash_rows_of_relocate(
        self, old_path: str, new_path: str
    ) -> List[Tuple[int, int]]:
        select_sql = (
            self._get_stmts_holder().select_crash_row_id_pair_after_relocate_stmt()
        )
        return self.__find_crash_id_pairs(
            select_sql, old_path=old_path, new_path=new_path
        )

    def find_crash_rows_of_class_rename(
        self, path: str, old_class: str, new_class: str
    ) -> List[Tuple[int, int]]:
        select_sql = (
            self._get_stmts_holder().select_crash_row_id_pair_after_rename_class_stmt()
        )
        return self.__find_crash_id_pairs(
            select_sql, old_class=old_class, new_class=new_class, path=path
        )

    def find_crash_rows_of_method_rename(
        self, method_id: int, new_name: str
    ) -> List[Tuple[int, int]]:
        select_sql = (
            self._get_stmts_holder().select_crash_row_id_pair_after_rename_method_stmt()
        )
        return self.__find_crash_id_pairs(
            select_sql, method_id=method_id, new_name=new_name
        )

    def delete_methods_by_id(self, method_id: int) -> None:
        delete_sql = self._get_stmts_holder().delete_row_by_id_stmt()
        exe_cursor = self._get_db_connection().execute(delete_sql, {"id": method_id})
        exe_cursor.close()
        return None

    def __update(self, sql: str, **parameters) -> None:
        exe_cursor = self._get_db_connection().execute(sql, parameters)
        exe_cursor.close()
        return None

    def update_path(self, old_path: str, new_path: str) -> None:
        update_sql = self._get_stmts_holder().update_file_path_stmt()
        return self.__update(update_sql, old_path=old_path, new_path=new_path)

    def update_class(self, path: str, old_class: str, new_class: str) -> None:
        update_sql = self._get_stmts_holder().update_class_name_stmt()
        return self.__update(
            update_sql, path=path, old_class=old_class, new_class=new_class
        )

    def update_name(self, method_id: int, new_name: str) -> None:
        update_sql = self._get_stmts_holder().update_simple_name_stmt()
        return self.__update(update_sql, method_id=method_id, new_name=new_name)
