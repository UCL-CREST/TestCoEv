from typing import Dict, Optional
from commits2sql.modification.change_identifier.change_utils import (
    CodeDiffer,
    ChangeClassifier,
    CodeAnalyser,
)


class ChangeIdentifier(object):

    __INSTANCE: Optional[object] = None
    __DIFFER: Optional[CodeDiffer] = None
    __CODE_BEFORE: Optional[str] = None
    __CODE_CURRENT: Optional[str] = None

    def __new__(cls, *args, **kw):
        if cls.__INSTANCE is None:
            cls.__INSTANCE = object.__new__(cls)
        return cls.__INSTANCE

    def __init__(self, code_before: str, code_current: str):
        if self.__DIFFER is None:
            self.__DIFFER = CodeDiffer()
        if code_before == self.__CODE_BEFORE and code_current == self.__CODE_CURRENT:
            return
        exe_code, diff_output = self.__DIFFER.compare(code_before, code_current)
        if not exe_code == 0:
            raise Exception(f"FAIL TO EXECUTION DIFF {diff_output}")
        self.__CODE_BEFORE = code_before
        self.__CODE_CURRENT = code_current
        self.__before = CodeAnalyser(code_before)
        self.__current = CodeAnalyser(code_current)
        self.__line_nums_dict: Dict[int, int] = dict()
        classifier = ChangeClassifier(diff_output)
        for old_char_num, new_char_num in classifier.match_char_num_dict.items():
            old_line_num = self.__before.get_line_num(old_char_num)
            new_line_num = self.__current.get_line_num(new_char_num)
            self.__line_nums_dict[old_line_num] = new_line_num
        return

    def __del__(self):
        del self.__DIFFER

    def new_classname_of(self, old_classname: str) -> Optional[str]:
        line_num_before = self.__before.get_line_num_of_class(old_classname)
        if line_num_before not in self.__line_nums_dict:
            return None
        line_num_current = self.__line_nums_dict[line_num_before]
        return self.__current.get_classname_at_line(line_num_current)

    def new_lines_num_of(self, old_line_num: int) -> Optional[int]:
        return (
            self.__line_nums_dict[old_line_num]
            if old_line_num in self.__line_nums_dict
            else None
        )
