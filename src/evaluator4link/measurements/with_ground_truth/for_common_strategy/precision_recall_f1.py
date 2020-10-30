from evaluator4link.measurements.with_ground_truth import (
    StrategyWithGroundTruthMeasurement,
)
from evaluator4link.measurements.with_ground_truth.meta_data_measurement_class_level import (
    StrategyWithGroundTruthMeasurementClassLevel,
)


class PrecisionRecallMeasurement(StrategyWithGroundTruthMeasurement):
    def __init__(self, path_to_db: str, path_to_csv: str, for_strategy: str):
        super().__init__(path_to_db, path_to_csv, for_strategy)
        self.__ground_truth_link_num = len(self._ground_truth_links)
        self.__valid_predict_link_num = len(self._valid_predict_links)
        self.__all_predict_link_num = len(self._predict_links)

    @property
    def precision(self) -> float:
        if self.__all_predict_link_num == 0:
            return 0
        return self.__valid_predict_link_num / self.__all_predict_link_num

    @property
    def recall(self) -> float:
        if self.__ground_truth_link_num == 0:
            return 0
        return self.__valid_predict_link_num / self.__ground_truth_link_num

    @property
    def f1_score(self) -> float:
        return self.fn_score(1)

    def fn_score(self, n) -> float:
        if self.precision == 0 and self.recall == 0:
            return 0
        return ((1 + n ** 2) * self.precision * self.recall) / (
            (n ** 2 * self.precision) + self.recall
        )

    def __str__(self) -> str:
        return str(
            {
                "precision": self.precision,
                "recall": self.recall,
                "f1_score": self.f1_score,
                "valid_predict_link_num (True Positive)": self.__valid_predict_link_num,
                "all_predict_link_num (True Positive + False Positive)": self.__all_predict_link_num,
                "ground_truth_link_num (True Positive + False Negative)": self.__ground_truth_link_num,
            }
        )


class PrecisionRecallMeasurementClassLevel(
    StrategyWithGroundTruthMeasurementClassLevel
):
    def __init__(self, path_to_db: str, path_to_csv: str, for_strategy: str):
        super().__init__(path_to_db, path_to_csv, for_strategy)
        self.__ground_truth_link_num = len(self._ground_truth_links)
        self.__valid_predict_link_num = len(self._valid_predict_links)
        self.__all_predict_link_num = len(self._predict_links)

    @property
    def precision(self) -> float:
        if self.__all_predict_link_num == 0:
            return 0
        return self.__valid_predict_link_num / self.__all_predict_link_num

    @property
    def recall(self) -> float:
        if self.__ground_truth_link_num == 0:
            return 0
        return self.__valid_predict_link_num / self.__ground_truth_link_num

    @property
    def f1_score(self) -> float:
        return self.fn_score(1)

    def fn_score(self, n) -> float:
        if self.precision == 0 and self.recall == 0:
            return 0
        return ((1 + n ** 2) * self.precision * self.recall) / (
            (n ** 2 * self.precision) + self.recall
        )

    def __str__(self) -> str:
        return str(
            {
                "precision": self.precision,
                "recall": self.recall,
                "f1_score": self.f1_score,
                "valid_predict_link_num (True Positive)": self.__valid_predict_link_num,
                "all_predict_link_num (True Positive + False Positive)": self.__all_predict_link_num,
                "ground_truth_link_num (True Positive + False Negative)": self.__ground_truth_link_num,
            }
        )
