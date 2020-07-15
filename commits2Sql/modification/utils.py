from enum import Enum


class ChangeType(Enum):
    NOCHANGE = 'match'
    UPDATE = 'update-node'
    CREATE = 'insert-tree'
    REMOVE = 'delete-tree'

    def __str__(self):
        return self.value
