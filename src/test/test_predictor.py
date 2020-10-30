import os
from sql2link.predictor import *

if __name__ == "__main__":
    path_to_comp0110 = os.path.expanduser("~/Project/PycharmProjects/comp0110")
    sql2linker = TraceabilityPredictor(f"{path_to_comp0110}/.tmp/jfreechart.db")
    sql2linker.run(LinkStrategy.COCREATE, LinkBase.FOR_COMMITS)
    sql2linker.run(LinkStrategy.COCHANGE, LinkBase.FOR_COMMITS)
    sql2linker.run(
        LinkStrategy.APRIORI,
        LinkBase.FOR_COMMITS,
        {
            "min_support_for_change": 2,
            "min_support_for_cochange": 1,
            "min_confidence": 0.1,
        },
    )
    sql2linker.run(LinkStrategy.COCREATE, LinkBase.FOR_WEEKS)
    sql2linker.run(LinkStrategy.COCHANGE, LinkBase.FOR_WEEKS)
    sql2linker.run(
        LinkStrategy.APRIORI,
        LinkBase.FOR_WEEKS,
        {
            "min_support_for_change": 2,
            "min_support_for_cochange": 1,
            "min_confidence": 0.1,
        },
    )
    # sql2linker.run_with_filter(
    #     LinkStrategy.APRIORI,
    #     LinkBase.FOR_COMMITS,
    #     parameters={
    #         'changes_count_max': 30,
    #         'changes_count_min': 2,
    #         'min_support_for_change': 2,
    #         'min_support_for_cochange': 1,
    #         'min_confidence': 0
    #     },
    #     is_for_all=True
    # )
    # sql2linker.run_class_level(
    #     LinkStrategy.COCHANGE,
    #     LinkBase.FOR_COMMITS,
    # )
    # sql2linker.run_class_level_with_filter(
    #     LinkStrategy.COCHANGE,
    #     LinkBase.FOR_COMMITS,
    #     parameters={
    #         'changes_count_max': 7,
    #         'changes_count_min': 2
    #     }
    # )
