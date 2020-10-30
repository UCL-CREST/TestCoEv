import re

import pandas
from typing import Dict, Tuple, Optional
from evaluator4link.measurements import AbstractMeasurement


class StrategyWithGroundTruthMeasurementClassLevel(AbstractMeasurement):

    __SELECT_PREDICT_FOR_SAME_CLASS_NAME = """
        SELECT tested_class, test_class, confidence_num
        FROM {strategy}
        WHERE tested_class Like :class_name 
            OR test_class LIKE :class_name
    """

    __EXTRACT_SHORT_NAME_FROM_LONG_NAME_REGEX = (
        r"^(?:.+::)*(?P<class_name>\w+)(?:<.*)?$"
    )

    __FLYWEIGHT_TRUTH_PANDAS: Optional[pandas.DataFrame] = None

    @property
    def _ground_truth_pandas(self) -> pandas.DataFrame:
        return self.__FLYWEIGHT_TRUTH_PANDAS

    def __init__(self, path_to_db: str, path_to_csv: str, for_strategy: str):
        if self.__FLYWEIGHT_TRUTH_PANDAS is None:
            self.__FLYWEIGHT_TRUTH_PANDAS = pandas.read_csv(path_to_csv)
        self.__strategy_name = for_strategy
        self._predict_links: Dict[Tuple[str, str], float] = dict()
        self._ground_truth_links: Dict[Tuple[str, str], float] = dict()
        self._valid_predict_links: Dict[Tuple[str, str], float] = dict()
        super().__init__(path_to_db)

    def _measure(self) -> None:
        for _, test_class, tested_class, _ in self._ground_truth_pandas.values:
            self._ground_truth_links[(tested_class, test_class)] = 1.0
            self._predict_links.update(self.__get_predicate_links_of(test_class))
        predicted_links_set = set(self._predict_links.keys())
        ground_truth_links_set = set(self._ground_truth_links.keys())
        valid_predict_links_set = predicted_links_set.intersection(
            ground_truth_links_set
        )
        self._valid_predict_links = {
            names: self._predict_links[names] for names in valid_predict_links_set
        }
        return None

    def __get_predicate_links_of(self, class_name: int) -> Dict[Tuple[str, str], float]:
        output = dict()
        cursor = self._predict_database.cursor()
        select_sql = self.__SELECT_PREDICT_FOR_SAME_CLASS_NAME.format(
            strategy=self.__strategy_name
        )
        all_links = cursor.execute(
            select_sql, {"class_name": f"%{class_name}%"}
        ).fetchall()
        for tested_class_long_name, test_class_long_name, confidence_num in all_links:
            tested_class = self.__class_name_extract(tested_class_long_name)
            test_class = self.__class_name_extract(test_class_long_name)
            output[(tested_class, test_class)] = confidence_num
        return output

    def __class_name_extract(self, class_long_name) -> Optional[str]:
        match = re.match(
            self.__EXTRACT_SHORT_NAME_FROM_LONG_NAME_REGEX, class_long_name
        )
        return match.group("class_name").lower() if match is not None else None

    @property
    def predict_links(self) -> Dict[Tuple[str, str], float]:
        return self._predict_links

    @property
    def ground_truth_links(self) -> Dict[Tuple[str, str], float]:
        return self._ground_truth_links

    @property
    def valid_predict_links(self) -> Dict[Tuple[str, str], float]:
        return self._valid_predict_links
