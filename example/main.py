import os
import zipfile
from datetime import datetime

from evaluator4link.evaluator import LinkEvaluator
from src import TraceabilityPredictor, LinkStrategy, LinkBase
from commits2sql.miner import DataMiner


def main():
    example_path = os.path.dirname(__file__)
    output_dir = f"{example_path}/output"
    input_dir = f"{example_path}/input"
    with zipfile.ZipFile(f"{input_dir}/commons_lang.zip", "r") as target_zip:
        # 0. Prepare target file and tool
        target_zip.extractall(input_dir)

        # 1. Mining
        repository_path = f"{input_dir}/commons_lang"
        miner = DataMiner(output_dir, repository_path)
        miner.mining(start_date=datetime(2020, 10, 1))
        # 2. Predicting
        database_path = f"{output_dir}/commons_lang.db"
        TraceabilityPredictor(database_path).run(
            LinkStrategy.COCHANGE, LinkBase.FOR_COMMITS
        )
        ground_truth_csv_path = f"{input_dir}/gt_commons_lang.csv"
        # 3. Evaluating
        evaluator = LinkEvaluator(database_path, ground_truth_csv_path)
        print(
            evaluator.precision_recall_and_f1_score_of_strategy(
                "links_commits_based_cochanged"
            )
        )


if __name__ == "__main__":
    main()
