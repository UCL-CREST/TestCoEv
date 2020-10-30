import re
import errno
import shutil
import subprocess
import tempfile
from typing import List, Tuple, Dict, Optional


class CodeAnalyser(object):

    __REGEX_CLASS_DECLARATION = (
        r"(?P<before_name>class\s+)"
        r"(?P<name>\w+(?:<.+>)?)"
        r"(?P<after_name>\s+(?:(?:implements|extends)\s+\S+\s+)?{)"
    )

    def __init__(self, code: str):
        self.code = code
        total_char_num = 0
        self.__line_num_char_num_dict: List[int] = [-1]
        for each_line in code.splitlines(True):
            self.__line_num_char_num_dict.append(total_char_num)
            total_char_num += len(each_line)
        self.__line_num_char_num_dict.append(total_char_num)
        self.line_num_classname_dict: Dict[int, str] = dict()
        for match in re.finditer(self.__REGEX_CLASS_DECLARATION, code):
            if match is not None and match.lastindex == 3:
                before_target = match.group("before_name")
                target = match.group("name")
                start = match.span()[0] + len(before_target)
                line_num = self.get_line_num(start)
                self.line_num_classname_dict[line_num] = target
        return

    def get_line_num(self, char_num: int) -> int:
        return self.__binary_search(char_num, 0, len(self.__line_num_char_num_dict))

    def __binary_search(self, char_num: int, start_line: int, end_line: int):
        if start_line >= end_line:
            return -1
        mid = (start_line + end_line) // 2
        if (
            self.__line_num_char_num_dict[mid]
            <= char_num
            < self.__line_num_char_num_dict[mid + 1]
        ):
            return mid
        if self.__line_num_char_num_dict[mid] > char_num:
            return self.__binary_search(char_num, start_line, mid)
        if self.__line_num_char_num_dict[mid + 1] < char_num:
            return self.__binary_search(char_num, mid + 1, end_line)

    def get_char_num_range(self, line_num: int) -> Optional[Tuple[int, int]]:
        if len(self.__line_num_char_num_dict) <= line_num + 1:
            return -1, -1
        start_of_target = self.__line_num_char_num_dict[line_num]
        end_of_target = self.__line_num_char_num_dict[line_num + 1] - 1
        return start_of_target, end_of_target

    def get_line_num_of_class(self, name: str) -> int:
        for line_num, class_name in self.line_num_classname_dict.items():
            if name == class_name:
                return line_num
        return -1

    def get_classname_at_line(self, num: int) -> Optional[str]:
        return (
            self.line_num_classname_dict[num]
            if num in self.line_num_classname_dict
            else None
        )


class CodeDiffer(object):
    __NAME_AFTER = "after"
    __NAME_BEFORE = "before"
    __SUFFIX = "java"
    __CMD_DIFF = "gumtree textdiff {before} {after}"

    def __init__(self, tmp_dir: str = None, gumtree_dir: str = None):
        self.__tmp_dir = tmp_dir if tmp_dir is not None else tempfile.mkdtemp()
        self.__gumtree_dir = gumtree_dir if gumtree_dir is not None else ""

    def __del__(self):
        try:
            if self.__tmp_dir is not None:
                shutil.rmtree(self.__tmp_dir)
        except OSError as exc:
            if exc.errno != errno.ENOENT:
                raise

    def compare(self, before: str, after: str) -> Tuple[int, str]:
        if before == after:
            return 0, ""
        path_before = f"{self.__tmp_dir}/{self.__NAME_BEFORE}.{self.__SUFFIX}"
        path_after = f"{self.__tmp_dir}/{self.__NAME_AFTER}.{self.__SUFFIX}"
        with open(path_before, "w") as f:
            f.write(before)
        with open(path_after, "w") as f:
            f.write(after)
        diff_cmd = self.__CMD_DIFF.format(before=path_before, after=path_after)
        gumtree_cmd = f"{self.__gumtree_dir} {diff_cmd}"
        return subprocess.getstatusoutput(gumtree_cmd)


class ChangeClassifier(object):
    __SPLIT_ALL_CHANGES = "===\n"
    __SPLIT_TYPE_DETAIL = "\n---\n"

    __TYPE_MATCH = "match"
    __TYPE_UPDATE = "update-node"
    __TYPE_INSERT = "insert-tree"
    __TYPE_DELETE = "delete-tree"

    __REGEX_MATCH_NAME = (
        r"^SimpleName: (?P<old_name>\w+) \[(?P<old_start>\d+),(?P<old_end>\d+)\]\s*"
        r"SimpleName: (?P<new_name>\w+) \[(?P<new_start>\d+),(?P<new_end>\d+)\]"
    )
    __REGEX_UPDATE_NAME = (
        r"^SimpleName:.*\[(?P<old_start>\d+),(?P<old_end>\d+)\]\s*"
        r"replace (?P<old_name>\w+) by (?P<new_name>\w+)"
    )
    __REGEX_NEW_OR_DEL = (
        r"^(?P<type>MethodDeclaration|TypeDeclaration) \[(?P<start>\d+),(?P<end>\d+)\]"
    )

    def __init__(self, diff_txt: str):
        matched, updated, inserted, deleted = list(), list(), list(), list()
        for change_diff in diff_txt.split(self.__SPLIT_ALL_CHANGES):
            change_type, _, change_detail = change_diff.partition(
                self.__SPLIT_TYPE_DETAIL
            )
            if change_type == self.__TYPE_MATCH:
                matched.append(change_detail)
            elif change_type == self.__TYPE_UPDATE:
                updated.append(change_detail)
            elif change_type == self.__TYPE_INSERT:
                inserted.append(change_detail)
            elif change_detail == self.__TYPE_DELETE:
                deleted.append(change_detail)
        names_match_char_num: Dict[int, int] = dict()
        for match_detail in matched:
            res = re.match(self.__REGEX_MATCH_NAME, match_detail)
            if res is None:
                continue
            res_dict = res.groupdict()
            if "old_start" not in res_dict or "new_start" not in res_dict:
                continue
            old_start, new_start = int(res_dict["old_start"]), int(
                res_dict["new_start"]
            )
            names_match_char_num[old_start] = new_start
        self.match_char_num_dict = names_match_char_num
        renamed_char_nums: Dict[int, int] = dict()
        for update_detail in updated:
            res = re.match(self.__REGEX_UPDATE_NAME, update_detail)
            if res is None:
                continue
            res_dict = res.groupdict()
            if res is None or "old_start" not in res_dict:
                continue
            old_start_char_num = int(res.group("old_start"))
            if old_start_char_num not in names_match_char_num:
                continue
            renamed_char_nums[old_start_char_num] = names_match_char_num[
                old_start_char_num
            ]
        self.updated_char_num_dict = renamed_char_nums
