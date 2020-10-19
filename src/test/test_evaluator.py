from matplotlib.backends.backend_pdf import PdfPages
import os
import sqlite3
import pandas as pd
from typing import List, Tuple, Dict, Optional, Set
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.axes import Axes
from mpl_toolkits.mplot3d import Axes3D
from pandas import DataFrame

from evaluator4link.evaluator import LinkEvaluator, FileCommitsCountMeasurement, ClassCommitsCountMeasurement, \
    TestedCommitsCountMeasurement, TestCommitsCountMeasurement, MethodCommitsCountMeasurement, CommitsDataMeasurement
from evaluator4link.measurements.with_ground_truth.for_common_strategy.precision_recall_f1 import \
    PrecisionRecallMeasurementClassLevel, PrecisionRecallMeasurement
from sql2link import TraceabilityPredictor, LinkStrategy, LinkBase



def draw_figure_for_co_changed(predicted_links: List[float]):
    plt.figure(num=1, figsize=(30, 5))
    X = np.arange(len(predicted_links))
    Y = np.array(predicted_links)
    plt.bar(X, Y, facecolor='#9999ff', edgecolor='white')
    for x, y in zip(X, Y): plt.text(x + 0.01, y + 0.05, '%.1f' % y, ha='center', va='top')
    plt.xlim((-1, len(predicted_links)))
    plt.ylim((0, 1.25))
    plt.xlabel("co_change_id")
    plt.ylabel("confidence")
    plt.show()


def __draw_scatter_from_dict(ax: Axes3D, dict: Dict[Tuple[int, int], float], color: str, marker: str, size: int):
    id_pairs = dict.keys()
    tested_ids = [id_pair[1] for id_pair in id_pairs]
    test_ids = [id_pair[0] for id_pair in id_pairs]
    predict_value = [value for value in dict.values()]
    zs = np.array(predict_value)
    xs = np.array(test_ids)
    ys = np.array(tested_ids)
    ax.scatter(xs, ys, zs, c=color, marker=marker, s=size)


def draw_3D_for_co_changed():
    evaluator = LinkEvaluator(path_to_db, path_to_csv)
    evaluation = evaluator.raw_links_for_predicated_and_ground_truth('apriori_for_weeks')
    num_of_links = len(evaluation.ground_truth_links)
    gt_links_id_pair = list(evaluation.ground_truth_links.keys())
    pd_links_dict = evaluation.predict_links
    valid_pd_links_dict = evaluation.valid_predict_links
    predicted_links: List[float] = list()
    for link in gt_links_id_pair:
        if link not in valid_pd_links_dict:
            predicted_links.append(0.0)
        else:
            predicted_links.append(valid_pd_links_dict[link])
    fig = plt.figure(num=1, figsize=(15, 15))
    ax1 = fig.add_subplot(111, projection='3d')
    __draw_scatter_from_dict(ax1, pd_links_dict, 'b', '.', 1)
    __draw_scatter_from_dict(ax1, valid_pd_links_dict, 'r', '^', 10)
    __draw_scatter_from_dict(ax1, evaluation.ground_truth_links, 'g', '^', 20)
    plt.title('sale')
    plt.xlabel("tested_id")
    plt.ylabel("test_id")
    plt.show()


def print_complete_report() -> None:
    evaluate_report = LinkEvaluator(path_to_db, path_to_csv)
    print(
        'links_commits_based_apriori: ',
        evaluate_report.precision_recall_and_f1_score_of_strategy('links_commits_based_apriori')
    )
    print(
        'links_commits_based_cochanged: ',
        evaluate_report.precision_recall_and_f1_score_of_strategy('links_commits_based_cochanged')
    )
    print(
        'links_commits_based_cocreated: ',
        evaluate_report.precision_recall_and_f1_score_of_strategy('links_commits_based_cocreated')
    )
    print(
        'links_weeks_based_apriori: ',
        evaluate_report.precision_recall_and_f1_score_of_strategy('links_weeks_based_apriori')
    )
    print(
        'links_weeks_based_cochanged: ',
        evaluate_report.precision_recall_and_f1_score_of_strategy('links_weeks_based_cochanged')
    )
    print(
        'links_weeks_based_cocreated: ',
        evaluate_report.precision_recall_and_f1_score_of_strategy('links_weeks_based_cocreated')
    )
    return None


def print_apriori_report() -> None:
    evaluate_report = LinkEvaluator(path_to_db, path_to_csv)
    print(evaluate_report.precision_recall_and_f1_score_of_strategy('apriori_for_commits'))
    print(evaluate_report.precision_recall_and_f1_score_of_strategy('apriori_for_weeks'))


def output_to_csv() -> None:
    evaluate_report = LinkEvaluator(path_to_db, path_to_csv)
    evaluate_report.output_predict_to_csv()


def draw_scatter_figure_for_coordinates_for_methods_and_commits_type():
    fig = plt.figure(num=1, figsize=(15, 15))
    axes = fig.add_subplot(111, projection='3d')

    def draw_3d_scatter(by_3d_coordinates: List[Tuple[int, int, int]], color: str, marker: str, size: int):
        xs, ys, zs = list(), list(), list()
        for x, y, z in by_3d_coordinates:
            xs.append(x)
            ys.append(y)
            zs.append(z)
        axes.scatter(np.array(xs), np.array(ys), np.array(zs), c=color, marker=marker, s=size)

    coordinates = LinkEvaluator(path_to_db, path_to_csv).coordinates_for_methods_commits()
    draw_3d_scatter(coordinates.coordinates_for_test, 'r', '.', 1)
    draw_3d_scatter(coordinates.coordinates_for_tested, 'b', '^', 1)
    print(coordinates.package_name_x_table)
    print(coordinates.commit_hash_y_table)
    print(coordinates.change_type_z_table)
    plt.title('sale')
    plt.xlabel("method_id")
    plt.ylabel("commit_id")
    plt.show()


def draw_2d_scatter_for_commits_distributions():

    def draw_2d_scatter_for_type_z(
            axes: Axes,
            by_3d_coordinates: List[Tuple[int, int, int]],
            title: str, y_max: Optional[int] = None
    ) -> None:
        added: Tuple[List[int], List[int]] = (list(), list())
        modified: Tuple[List[int], List[int]] = (list(), list())
        renamed: Tuple[List[int], List[int]] = (list(), list())
        for change_commit, change_count, change_type in by_3d_coordinates:
            if y_max is not None and change_count > y_max:
                print(f'IGNORE COMMITS({change_commit}), SIZE ({change_count}), TYPE({change_type}).')
                continue
            if change_type == 1:
                added[0].append(change_commit)
                added[1].append(change_count)
            elif change_type == 2:
                modified[0].append(change_commit)
                modified[1].append(change_count)
            elif change_type == 3:
                renamed[0].append(change_commit)
                renamed[1].append(change_count)
        axes.scatter(np.array(added[0]), np.array(added[1]), c='r', marker='.', s=1)
        axes.scatter(np.array(modified[0]), np.array(modified[1]), c='b', marker='.', s=1)
        axes.scatter(np.array(renamed[0]), np.array(renamed[1]), c='g', marker='.', s=1)
        axes.set_xlabel("commits_id(chronological)")
        axes.set_ylabel("number of changed (R: ADD, B: MODIFY, G: RENAME)")
        axes.set_title(title)
        return None

    evaluate_report = LinkEvaluator(path_to_db, path_to_csv)
    files = evaluate_report.coordinates_for_files_changes_distribution_of_commits().commits_count_coordinates
    classes = evaluate_report.coordinates_for_classes_changes_distribution_of_commits().commits_count_coordinates
    methods = evaluate_report.coordinates_for_methods_changes_distribution_of_commits().commits_count_coordinates
    test = evaluate_report.coordinates_for_test_changes_distribution_of_commits().commits_count_coordinates
    tested = evaluate_report.coordinates_for_tested_changes_distribution_of_commits().commits_count_coordinates

    fig = plt.figure(num=5, figsize=(25, 25))
    draw_2d_scatter_for_type_z(fig.add_subplot(511), files, 'changes for files', 5)
    draw_2d_scatter_for_type_z(fig.add_subplot(512), classes, 'changes for classes', 5)
    draw_2d_scatter_for_type_z(fig.add_subplot(513), methods, 'changes for methods', 25)
    draw_2d_scatter_for_type_z(fig.add_subplot(514), test, 'changes for test', 25)
    draw_2d_scatter_for_type_z(fig.add_subplot(515), tested, 'changes for tested', 25)
    plt.show()


def draw_2d_fig_for_test_and_tested_and_commits(project_name: str):
    path_to_comp0110 = os.path.expanduser('~/Project/PycharmProjects/comp0110')
    path_to_tmp = f'{path_to_comp0110}/.tmp'
    path_to_db = f'{path_to_tmp}/{project_name}.db'
    methods = CommitsDataMeasurement(path_to_db)
    tests_coord = methods.coordinates_for_test
    testeds_coord = methods.coordinates_for_tested

    def __classify_changes(coord: List[Tuple[int, int, int]], color: str, size: int):
        added, modified, renamed = (list(), list()), (list(), list()), (list(), list())
        for method_y, commit_x, type_c in coord:
            stored = None
            if type_c == 1: stored = added
            elif type_c == 2: stored = modified
            elif type_c == 3: stored = renamed
            if stored is None: continue
            stored[0].append(commit_x)
            stored[1].append(method_y)
        plt.scatter(np.array(added[0]), np.array(added[1]), c=color, marker='+', s=size, alpha=0.5)
        plt.scatter(np.array(modified[0]), np.array(modified[1]), c=color, marker='^', s=size, alpha=0.5)
        plt.scatter(np.array(renamed[0]), np.array(renamed[1]), c=color, marker='*', s=size, alpha=0.5)

    test_changes_commits = {commit_x for method_y, commit_x, type_c in tests_coord}
    tested_changes_commits = {commit_x for method_y, commit_x, type_c in testeds_coord}
    valid_commits = test_changes_commits.union(tested_changes_commits)
    co_changed_commits = test_changes_commits.intersection(tested_changes_commits)
    print('valid', len(valid_commits))
    print('co_changed', len(co_changed_commits))
    __classify_changes(testeds_coord, color='red', size=10)
    __classify_changes(tests_coord, color='blue', size=10)
    plt.savefig(f"changes_history_view_{project_name}.pdf", bbox_inches='tight')
    plt.show()


def draw_box_plot_for_changes_in_commits(
    path_to_db: str, specific_test_path: str = 'src/test%', specific_tested_path: str = 'src/main%'
):
    files = FileCommitsCountMeasurement(path_to_db,specific_test_path,specific_tested_path)
    classes = ClassCommitsCountMeasurement(path_to_db,specific_test_path,specific_tested_path)
    testeds = TestedCommitsCountMeasurement(path_to_db,specific_test_path,specific_tested_path)
    tests = TestCommitsCountMeasurement(path_to_db,specific_test_path,specific_tested_path)
    methods = MethodCommitsCountMeasurement(path_to_db,specific_test_path,specific_tested_path)
    fig = plt.figure(num=5, figsize=(25, 25))

    def __draw_box_plot(
            axes: Axes,
            change_coordinates: List[Tuple[int, int, int]],
            title: str,
    ) -> None:
        added_dict, modified_dict, renamed_dict, total_dict = dict(), dict(), dict(), dict()
        for commit_x, count_y, type_c in change_coordinates:
            added_dict.setdefault(commit_x, 0)
            modified_dict.setdefault(commit_x, 0)
            renamed_dict.setdefault(commit_x, 0)
            total_dict.setdefault(commit_x, 0)
            if type_c == 1:
                added_dict[commit_x] = count_y
            elif type_c == 2:
                modified_dict[commit_x] = count_y
            elif type_c == 3:
                renamed_dict[commit_x] = count_y
            else:
                continue
            total_dict[commit_x] += count_y
        added = [count for count in added_dict.values()]
        modified = [count for count in modified_dict.values()]
        renamed = [count for count in renamed_dict.values()]
        total = [count for count in total_dict.values()]
        axes.set_title(title)
        axes.boxplot(
            x=[added, modified, renamed, total],
            labels=('added', 'modified', 'renamed', 'total'),
            showfliers=False
        )
        return None

    __draw_box_plot(fig.add_subplot(511), files.commits_count_coordinates, 'changes for files')
    __draw_box_plot(fig.add_subplot(512), classes.commits_count_coordinates, 'changes for classes')
    __draw_box_plot(fig.add_subplot(513), methods.commits_count_coordinates, 'changes for methods')
    __draw_box_plot(fig.add_subplot(514), tests.commits_count_coordinates, 'changes for test')
    __draw_box_plot(fig.add_subplot(515), testeds.commits_count_coordinates, 'changes for tested')
    plt.show()


def theory_max_precision():
    evaluator = LinkEvaluator(path_to_db, path_to_csv)
    report = evaluator.co_changed_commits()
    co_changes_commits = report.co_changes_commits

    commit_method_pairs: Dict[str, Set[Tuple[int, int]]] = dict()
    for method_pair, commit_ids in co_changes_commits.items():
        for commit_id in commit_ids:
            commit_hash = report.from_commit_id_to_hash(commit_id)
            commit_method_pairs.setdefault(commit_hash, set())
            commit_method_pairs[commit_hash].add(method_pair)

    path_to_gt_count = f'{path_to_tmp}/table_for_ground_truth_occurred_commits.csv'
    csv_data = pd.read_csv(path_to_gt_count, index_col=0)
    commits_count: Dict[str, int] = dict()
    for commits in co_changes_commits.values():
        for commit_id in commits:
            commit_hash = report.from_commit_id_to_hash(commit_id)
            commit_count = csv_data.loc[commit_hash][-2]
            if commit_hash in commits_count: continue
            if commit_count > 14 or commit_count < 3: continue
            commits_count[commit_hash] = commit_count

    sorted_commits = sorted(commits_count.keys(), key=lambda hash_val: (commits_count[hash_val]))
    min_commits = set()
    cur_methods_scope = set()
    for commit_hash in sorted_commits:
        method_pairs = commit_method_pairs[commit_hash]
        if cur_methods_scope.issuperset(method_pairs):
            continue
        cur_methods_scope.update(method_pairs)
        min_commits.add(commit_hash)

    db_connection = sqlite3.connect(path_to_db)

    def find_all_links_in_commits(commit_hash: str) -> Set[Tuple[int, int]]:
        db_cursor = db_connection.cursor()
        exe_rst = db_cursor.execute(f'''
            WITH test_methods AS (
                SELECT id FROM git_methods
                WHERE file_path LIKE 'src/test/java/org/apache/commons/lang3%'
            ), tested_functions AS (
                SELECT id FROM git_methods
                WHERE file_path LIKE 'src/main/java/org/apache/commons/lang3%'
            ), changes_test_in_commits AS (
                SELECT target_method_id AS test_id FROM  git_changes
                WHERE commit_hash = :commit_hash
                AND target_method_id IN test_methods
            ), changes_tested_in_commits AS (
                SELECT target_method_id AS tested_id FROM  git_changes
                WHERE commit_hash = :commit_hash
                AND target_method_id IN tested_functions
            )
            SELECT DISTINCT tested_id, test_id
            FROM changes_test_in_commits
            LEFT OUTER JOIN changes_tested_in_commits
        ''', {'commit_hash': commit_hash})
        return {(int(row[0]), int(row[1])) for row in exe_rst.fetchall() if row is not None and len(row) == 2}

    predicated_pairs = set()
    test_ids = set(report.test_changed_commits.keys())
    for commit_hash in min_commits:
        candidate = find_all_links_in_commits(commit_hash)
        for pair in candidate:
            if pair[1] in test_ids: predicated_pairs.add(pair)

    print(len(predicated_pairs))


def loop_for_precision(
    path_to_db: str,
    path_to_csv: str,
    max_range: range,
    test_path: str = 'src/test%',
    tested_path: str = 'src/main%',
    is_verbose: bool = False
):
    sql2linker = TraceabilityPredictor(path_to_db)
    cochanged_res = 'links_filtered_commits_based_cochanged'
    reports = list()
    for total_max in max_range:
        sql2linker.run_with_filter(
            LinkStrategy.COCHANGE,
            LinkBase.FOR_COMMITS,
            parameters={
                'changes_count_max': total_max,
                'changes_count_min': 0,
                'test_path': test_path,
                'tested_path': tested_path
            },
            is_previous_ignored=True,
            is_for_all=True
        )
        report = PrecisionRecallMeasurement(path_to_db, path_to_csv, cochanged_res)
        if is_verbose: print(total_max, report)
        reports.append(report)
    X_es = max_range
    Y_precisions = np.array([report.precision for report in reports])
    Y_recalls = np.array([report.recall for report in reports])
    Y_f1s = np.array([report.f1_score for report in reports])
    f=plt.figure(num=1, figsize=(10, 5))
    plt.plot(X_es, Y_precisions, color='red', linewidth=1, label='Precision')
    plt.plot(X_es, Y_recalls, color='blue', linestyle='--', linewidth=1, label='Recall')
    plt.plot(X_es, Y_f1s, color='orange', linestyle='-.', linewidth=1, label='F1 Score')
    plt.xlabel('Max Change Count')
    plt.ylabel('Measurements')
    plt.legend(loc='upper right')
    f.savefig(f"{path_to_db.split('/')[-1]}.pdf", bbox_inches='tight')
    plt.close()

if __name__ == '__main__':
    path_to_comp0110 = os.path.expanduser('~/Project/PycharmProjects/comp0110')
    path_to_tmp = f'{path_to_comp0110}/.tmp'
    path_to_db = f'{path_to_tmp}/commons_lang.db'
    path_to_csv = f'{path_to_tmp}/commons-lang-oracle-method-links.csv'
    strategy = 'links_commits_based_apriori'
    TraceabilityPredictor(path_to_db).run(
        strategy=LinkStrategy.APRIORI,
        base=LinkBase.FOR_COMMITS,
        parameters={
            'min_test_changes_support': 3,
            'min_tested_changes_support': 1,
            'min_coevolved_changes_support': 2,
            'min_confidence': 0.5
        },
        is_previous_ignored=True
    )
    print(PrecisionRecallMeasurement(path_to_db, path_to_csv, strategy))


















