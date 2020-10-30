from typing import Optional, List

from commits2sql.modification.change_holder.abstract_holder import AbstractHolder
from commits2sql.modification.change_holder.method_holder import MethodHolder


class ClassHolder(AbstractHolder):
    def __init__(self, before: Optional[str], current: Optional[str]):
        self.name_before: Optional[str] = before
        self.name_current: Optional[str] = current
        self.methods: List[MethodHolder] = list()

    def is_new(self) -> bool:
        return (self.name_before is None) and (self.name_current is not None)

    def is_deleted(self) -> bool:
        return (self.name_before is not None) and (self.name_current is None)

    def is_renamed(self) -> bool:
        return (
            (self.name_before is not None)
            and (self.name_current is not None)
            and (self.name_before != self.name_current)
        )

    def is_modified(self) -> bool:
        for method in self.methods:
            if method.is_changed():
                return True
        return False
