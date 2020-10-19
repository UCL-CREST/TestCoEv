from typing import List, Dict, Tuple, Set, Optional
from evaluator4link.measurements.with_ground_truth.for_co_changed_only import AbstractCoChangeMetaDataMeasurement


class CoChangedCommitMeasurement(AbstractCoChangeMetaDataMeasurement):

    @property
    def _select_method_changes_sql_stmt(self) -> str: return '''
        SELECT DISTINCT commit_hash FROM git_changes
        WHERE target_method_id = :method_id
    '''

    @property
    def test_changed_commits(self) -> Dict[int, Set[int]]:
        return self.__test_changed_commits

    @property
    def tested_changed_commits(self) ->  Dict[int, Set[int]]:
        return self.__tested_changed_commits

    @property
    def co_changes_commits(self) -> Dict[Tuple[int, int], Set[int]]:
        return self.__co_changed_commits

    @property
    def commit_hash_to_id_mapping(self) -> Dict[str, int]:
        return self.__hash_val_id_mapping

    def __init__(self, path_to_db: str, path_to_csv: str):
        super().__init__(path_to_db, path_to_csv, 'links_commits_based_cochanged')
        self.__hash_val_id_mapping: Dict[str, int] = dict()
        self.__test_changed_commits = {
            method_id: {self.from_hash_value_to_id(hash_val) for hash_val in hash_vals}
            for method_id, hash_vals in self._test_changes.items()
        }
        self.__tested_changed_commits = {
            method_id: {self.from_hash_value_to_id(hash_val) for hash_val in hash_vals}
            for method_id, hash_vals in self._tested_changes.items()
        }
        self.__co_changed_commits = {
            method_pair: {self.from_hash_value_to_id(hash_val) for hash_val in hash_vals}
            for method_pair, hash_vals in self._co_changes.items()
        }

    def from_commit_id_to_hash(self, target_id: int) -> Optional[str]:
        for commit_hash, commit_id in self.__hash_val_id_mapping.items():
            if commit_id == target_id: return commit_hash
        return None

    def from_hash_value_to_id(self, hash_val: str) -> int:
        self.__hash_val_id_mapping.setdefault(hash_val, len(self.__hash_val_id_mapping) + 1)
        return self.__hash_val_id_mapping[hash_val]

    def __str__(self):
        return str({
            'test_changed_commits': self.__test_changed_commits,
            'tested_changed_commits': self.__tested_changed_commits,
            'co_changed_commits': self.__co_changed_commits,
            'hash_val_id_mapping': self.__hash_val_id_mapping
        })
