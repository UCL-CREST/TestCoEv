from typing import Optional, Set, List

from commits2sql.modification.change_holder.abstract_holder import AbstractHolder
from commits2sql.modification.change_holder.class_holder import ClassHolder


class FileHolder(AbstractHolder):
    def __init__(self, before: Optional[str], current: Optional[str]):
        self.path_before: Optional[str] = before
        self.path_current: Optional[str] = current
        self.classes: List[ClassHolder] = list()

    def is_renamed(self) -> bool:
        return (
            (self.path_before is not None)
            and (self.path_current is not None)
            and (self.path_before != self.path_current)
        )
