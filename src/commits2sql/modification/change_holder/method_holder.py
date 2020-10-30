from typing import Optional, List

from pydriller.domain.commit import Method

from commits2sql.modification.change_holder.abstract_holder import AbstractHolder


class MethodHolder(AbstractHolder):
    def __init__(self, before: Optional[Method], current: Optional[Method]):
        self.method_before: Optional[Method] = before
        self.method_current: Optional[Method] = current

    def is_new(self) -> bool:
        return (self.method_before is None) and (self.method_current is not None)

    def is_deleted(self) -> bool:
        return (self.method_before is not None) and (self.method_current is None)

    def is_renamed(self) -> bool:
        return (
            (self.method_before is not None)
            and (self.method_current is not None)
            and (self.method_before.long_name != self.method_current.long_name)
        )

    def is_modified(self) -> bool:
        return (
            (self.method_before is not None)
            and (self.method_current is not None)
            and (self.method_before.long_name == self.method_current.long_name)
        )

    def is_changed(self) -> bool:
        return True
