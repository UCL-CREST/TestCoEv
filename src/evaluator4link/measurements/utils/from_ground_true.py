import re
from evaluator4link.measurements.utils import AbsMethodNameExtractor


class GroundTruthMethodName(AbsMethodNameExtractor):

    __INIT_NAME_REPLAY_REGEX = (
        r"(?P<name>\w+?)\.(?P<init_fun><init>\()",
        r"\g<name>.\g<name>(",
    )

    __CLASS_METHOD_NAME_REGEX = (
        r"^(?P<sub_path>[a-z.\d]+)\."
        r"(?P<class_names>[\w.]+)\."
        r"(?P<method_signature>(?P<simple_name>\w+)?(?:<.+>)?\(.*\))"
    )

    __SUPER_PACKAGE_NAME_REGEX = r"(?P<super_name>[^,(<>]*\.)"

    def __init__(self, long_name: str):
        long_name = re.sub(
            self.__INIT_NAME_REPLAY_REGEX[0],
            self.__INIT_NAME_REPLAY_REGEX[1],
            long_name,
        )
        self.__long_name = long_name
        match = re.match(self.__CLASS_METHOD_NAME_REGEX, long_name)
        if match is None:
            match_names = {
                "sub_path": "",
                "class_names": "",
                "method_signature": long_name,
                "simple_name": long_name,
            }
        else:
            match_names = match.groupdict()
        self.__file_path = match_names["sub_path"].replace(".", "/")
        self.__class_name = match_names["class_names"].replace(".", "::")
        signature_match = re.sub(
            self.__SUPER_PACKAGE_NAME_REGEX, "", match_names["method_signature"]
        )
        self.__signature = signature_match.replace(" ", "")
        self.__simple_name = match_names["simple_name"]

    @property
    def file_path(self) -> str:
        return self.__file_path

    @property
    def class_name(self) -> str:
        return self.__class_name

    @property
    def simple_name(self) -> str:
        return self.__simple_name

    @property
    def signature(self) -> str:
        return self.__signature

    @property
    def long_name(self) -> str:
        return self.__long_name
