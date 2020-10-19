import re
import logging
from typing import Dict, List, Tuple, Optional, Set

from pydriller import Modification
from pydriller.domain.commit import Method
from commits2sql.modification import ClassHolder, FileHolder, MethodHolder, ChangeIdentifier


class Extractor(object):

    __CLASS_METHOD_REGEX = r'^(?:(?P<class_name>.*)::)*(?P<method_name>\w+(?:<.*>)?\(.*\))$'
    __CLASS_NAME_REGEX = r'^(?:(?P<super_name>.*)::)*(?P<class_name>\w+(?:<.*>)?)$'

    def __init__(self, modification: Modification):
        self.__file = modification

    def get_changed_file(self) -> FileHolder:
        return self.__handle_file()

    def __handle_file(self) -> FileHolder:
        result = FileHolder(self.__file.old_path, self.__file.new_path)
        classes_dict_before = self.__collect_method(self.__file.methods_before)
        classes_dict_current = self.__collect_method(self.__file.methods)
        classes_dict_changed = self.__collect_method(self.__file.changed_methods)
        classified_classnames = self.__classify_classnames(
            set(classes_dict_before.keys()),
            set(classes_dict_current.keys()),
            set(classes_dict_changed.keys())
        )
        removed_classnames, created_classnames, unrenamed_classnames, renamed_classnames = classified_classnames
        for classname in removed_classnames:
            methods = classes_dict_before[classname]
            new_class_holder = ClassHolder(classname, None)
            for each in methods: new_class_holder.methods.append(MethodHolder(each, None))
            result.classes.append(new_class_holder)
        for classname in created_classnames:
            methods = classes_dict_current[classname]
            new_class_holder = ClassHolder(None, classname)
            for each in methods: new_class_holder.methods.append(MethodHolder(None, each))
            result.classes.append(new_class_holder)
        for classname in unrenamed_classnames:
            if classname not in classes_dict_changed: continue
            methods_before = self.__from_methods_to_name_dict(classes_dict_before[classname])
            methods_current = self.__from_methods_to_name_dict(classes_dict_current[classname])
            methods_changed = self.__from_methods_to_name_dict(classes_dict_changed[classname])
            classified_names = self.__classify_methods(methods_before, methods_current, methods_changed)
            removed_methodnames, created_methodnames, unrenamed_methodnames, renamed_methodnames = classified_names
            new_class_holder = ClassHolder(classname, classname)
            for name in removed_methodnames:
                new_class_holder.methods.append(MethodHolder(methods_before[name], None))
            for name in created_methodnames:
                new_class_holder.methods.append(MethodHolder(None, methods_current[name]))
            for name in unrenamed_methodnames:
                new_class_holder.methods.append(MethodHolder(methods_before[name], methods_current[name]))
            for before_name, after_name in renamed_methodnames.items():
                new_class_holder.methods.append(MethodHolder(methods_before[before_name], methods_current[after_name]))
            result.classes.append(new_class_holder)
        for classname_before, classname_current in renamed_classnames.items():
            methods_before = self.__from_methods_to_name_dict(classes_dict_before[classname_before])
            methods_current = self.__from_methods_to_name_dict(classes_dict_current[classname_current])
            changed_before = classes_dict_changed[classname_before] if classname_before in classes_dict_changed else []
            changed_current = classes_dict_changed[classname_current] if classname_current in classes_dict_changed else []
            methods_changed = self.__from_methods_to_name_dict(changed_before + changed_current)
            classified_names = self.__classify_methods(methods_before, methods_current, methods_changed)
            removed_methodnames, created_methodnames, unrenamed_methodnames, renamed_methodnames = classified_names
            new_class_holder = ClassHolder(classname_before, classname_current)
            for name in removed_methodnames:
                new_class_holder.methods.append(MethodHolder(methods_before[name], None))
            for name in created_methodnames:
                new_class_holder.methods.append(MethodHolder(None, methods_current[name]))
            for name in unrenamed_methodnames:
                new_class_holder.methods.append(MethodHolder(methods_before[name], methods_current[name]))
            for before_name, after_name in renamed_methodnames.items():
                new_class_holder.methods.append(MethodHolder(methods_before[before_name], methods_current[after_name]))
            result.classes.append(new_class_holder)
        return result

    def __collect_method(self, methods: List[Method]) -> Dict[str, List[Method]]:
        output: Dict[str:List[Method]] = dict()
        for method in methods:
            match = re.match(self.__CLASS_METHOD_REGEX, method.long_name)
            if match is None:
                logging.warning(f'method name {method.long_name} is not formatted as expected (ClassName::MethodName).')
                continue
            match_names = match.groupdict()
            match_names.setdefault('class_name', 'None')
            class_name = match_names['class_name'] if match_names['class_name'] is not None else 'None'
            output.setdefault(class_name, list())
            output[class_name].append(method)
        return output

    def __classify_classnames(
            self, before: Set[str], current: Set[str], changed: Set[str]
    ) -> Tuple[Set[str], Set[str], Set[str], Dict[str, str]]:
        unrenamed = (before & current)  # MD(Non-RN), Non-MD (Non-RN)
        removed_and_old = before - unrenamed  # RN_old(MD, Non-MD), RM
        created_and_new = current - unrenamed  # RN_new(MD, Non-MD), CT
        renamed: Dict[str, str] = dict()
        if len(removed_and_old) == 0 or len(created_and_new) == 0:
            return removed_and_old, created_and_new, changed & unrenamed, renamed
        identifier = ChangeIdentifier(self.__file.source_code_before, self.__file.source_code)
        old_list = sorted(removed_and_old, key=lambda it: len(it))
        for old_name in old_list:
            match = re.match(self.__CLASS_NAME_REGEX, old_name)
            if match is None or 'class_name' not in match.groupdict(): continue
            match_names = match.groupdict()
            old_class_name = match_names['class_name']
            old_super_name = match_names['super_name'] if 'super_name' in match_names else None
            new_class_name = identifier.new_classname_of(old_class_name)
            if new_class_name is None: continue
            new_super_name = renamed[old_super_name] if old_super_name in renamed else old_super_name
            new_name = f'{new_super_name}::{new_class_name}' if new_super_name is not None else new_class_name
            if new_name == old_name:
                for any_name in created_and_new:
                    match = re.match(self.__CLASS_NAME_REGEX, any_name)
                    if match is None or 'class_name' not in match.groupdict(): continue
                    tmp_class_name = match.group('class_name')
                    if tmp_class_name == new_name: new_name = any_name
                    if new_name == any_name: break
            if new_name not in created_and_new:
                logging.warning(f'class {new_name} was expected new name {old_name} (Now handled as added).')
                continue
            removed_and_old.remove(old_name)
            created_and_new.remove(new_name)
            renamed[old_name] = new_name
        return removed_and_old, created_and_new, changed & unrenamed, renamed

    def __from_methods_to_name_dict(self, methods: List[Method]):
        output: Dict[str:Method] = dict()
        for method in methods:
            match_names = re.match(self.__CLASS_METHOD_REGEX, method.long_name).groupdict()
            method_name = match_names['method_name']
            output[method_name] = method
        return output

    def __classify_methods(self,
        before: Dict[str, Method], current: Dict[str, Method], changed: Dict[str, Method]
    ) -> Tuple[Set[str], Set[str], Set[str], Dict[str, str]]:
        names_before = set(before.keys()) # MD(RN_old, Non-RN), Non-MD(RN_old, Non-RN), RM
        names_current = set(current.keys()) # MD(RN_new, Non-RN), Non-MD(RN_new, Non-RN), CT
        names_changed = set(changed.keys()) # RM, CT, MD(RN_new, Non-RN)
        names_unrenamed = (names_before & names_current)  # MD(Non-RN), Non-MD (Non-RN)
        names_removed_and_old = names_before - names_unrenamed  # RN_old(MD, Non-MD), RM
        names_created_and_new = names_current - names_unrenamed  # RN_new(MD, Non-MD), CT
        names_renamed: Dict[str, str] = dict()
        if len(names_removed_and_old) == 0 or len(names_created_and_new) == 0:
            return names_removed_and_old, names_created_and_new, names_unrenamed & names_changed, names_renamed
        identifier = ChangeIdentifier(self.__file.source_code_before, self.__file.source_code)
        for old_name in names_removed_and_old.copy():
            new_method_start_line = identifier.new_lines_num_of(before[old_name].start_line)
            new_name: Optional[str] = None
            for name in names_created_and_new:
                if new_name is not None: break
                if name not in changed: continue
                if changed[name].start_line != new_method_start_line: continue
                new_name = name
            if new_name is None: continue
            names_renamed[old_name] = new_name
            names_removed_and_old.remove(old_name)
            names_created_and_new.remove(new_name)
        return names_removed_and_old, names_created_and_new, names_unrenamed & names_changed, names_renamed
