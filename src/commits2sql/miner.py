import logging
from datetime import datetime
from typing import Optional

from pydriller import RepositoryMining
from pydriller.domain.commit import Modification
from commits2sql.database import TableHandlerFactory, Recorder
from commits2sql.modification import Extractor


class DataMiner(object):
    def __init__(
        self,
        tmp_data_dir: str,
        repos_path: str,
    ):
        repos_name = repos_path.rpartition("/")[-1]
        self.__recorder = Recorder(TableHandlerFactory(tmp_data_dir, repos_name))
        self.__repos_path = repos_path

    def mining(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        from_commit: Optional[str] = None,
        to_commit: Optional[str] = None,
    ) -> None:
        repos = RepositoryMining(
            self.__repos_path,
            since=start_date,
            to=end_date,
            from_commit=from_commit,
            to_commit=to_commit,
        )
        for commit in repos.traverse_commits():
            if self.__recorder.is_record_before(commit.hash):
                continue
            for modification in commit.modifications:
                self.__handle_modification(modification, commit.hash)
            self.__recorder.record_git_commit(commit.hash, commit.author_date)
        return None

    def __handle_modification(
        self, modification: Modification, commit_hash: str
    ) -> None:
        file = Extractor(modification).get_changed_file()
        if file.is_renamed():
            self.__recorder.record_file_relocate(file.path_before, file.path_current)
        path = file.path_current if file.path_current is not None else file.path_before
        for f_class in file.classes:
            if f_class.is_renamed():
                self.__recorder.record_rename_class(
                    path, f_class.name_before, f_class.name_current
                )
            class_name = (
                f_class.name_current
                if f_class.name_current is not None
                else f_class.name_before
            )
            for method in f_class.methods:
                if method.is_renamed():
                    before, current = method.method_before, method.method_current
                    old_name, cur_name = before.long_name, current.long_name
                    before_id = self.__recorder.get_method_id(
                        old_name, class_name, path
                    )
                    try:
                        self.__recorder.record_rename_method(
                            before_id, cur_name, commit_hash
                        )
                    except:
                        logging.warning(
                            f"error for renaming method_{before_id}: from {old_name} to ({cur_name})"
                        )
                elif method.is_new():
                    new_id = self.__recorder.get_method_id(
                        method.method_current.long_name, class_name, path
                    )
                    self.__recorder.record_add_method(new_id, commit_hash)
                elif method.is_deleted():
                    before_id = self.__recorder.get_method_id(
                        method.method_before.long_name, class_name, path
                    )
                    self.__recorder.record_remove_method(before_id)
                elif method.is_modified():
                    method_id = self.__recorder.get_method_id(
                        method.method_before.long_name, class_name, path
                    )
                    self.__recorder.record_modify_method(method_id, commit_hash)
        return None
