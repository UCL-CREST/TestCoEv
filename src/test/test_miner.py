import os
from commits2sql.miner import DataMiner
from sql2link import TraceabilityPredictor, LinkStrategy, LinkBase


def mining_commons_io():
    path_to_comp0110 = os.path.expanduser('~/Project/PycharmProjects/comp0110')
    DataMiner(
        f'{path_to_comp0110}/.tmp',
        f'{path_to_comp0110}/example_repositories/commons-io'
    ).mining(to_commit='54eeaee27c4d73a5b3b6ee84e53ee9046919a18b')
    sql2linker = TraceabilityPredictor(f'{path_to_comp0110}/.tmp/commons_io.db')
    sql2linker.run(LinkStrategy.COCREATE, LinkBase.FOR_COMMITS)
    sql2linker.run(LinkStrategy.COCHANGE, LinkBase.FOR_COMMITS)
    sql2linker.run(LinkStrategy.COCREATE, LinkBase.FOR_WEEKS)
    sql2linker.run(LinkStrategy.COCHANGE, LinkBase.FOR_WEEKS)


def mining_jfreechart():
    path_to_comp0110 = os.path.expanduser('~/Project/PycharmProjects/comp0110')
    DataMiner(
        f'{path_to_comp0110}/.tmp',
        f'{path_to_comp0110}/example_repositories/jfreechart'
    ).mining(to_commit='b3f5f21ba0fe32a8f7eccb6760a79df30628be3e')
    sql2linker = TraceabilityPredictor(f'{path_to_comp0110}/.tmp/jfreechart.db')
    specific_paths = {'tested_path': 'source/org/jfree/chart/%', 'test_path': 'tests/org/jfree/chart/%'}
    sql2linker.run(LinkStrategy.COCREATE, LinkBase.FOR_COMMITS, parameters=specific_paths)
    sql2linker.run(LinkStrategy.COCHANGE, LinkBase.FOR_COMMITS, parameters=specific_paths)
    sql2linker.run(LinkStrategy.COCREATE, LinkBase.FOR_WEEKS, parameters=specific_paths)
    sql2linker.run(LinkStrategy.COCHANGE, LinkBase.FOR_WEEKS, parameters=specific_paths)


def mining_ant():
    path_to_comp0110 = os.path.expanduser('~/Project/PycharmProjects/comp0110')
    DataMiner(
        f'{path_to_comp0110}/.tmp',
        f'{path_to_comp0110}/example_repositories/ant'
    ).mining(to_commit='d769172a135b19064dccb660b703ecf08f967e3e')
    sql2linker = TraceabilityPredictor(f'{path_to_comp0110}/.tmp/ant.db')
    sql2linker.run(LinkStrategy.COCREATE, LinkBase.FOR_COMMITS)
    sql2linker.run(LinkStrategy.COCHANGE, LinkBase.FOR_COMMITS)
    sql2linker.run(LinkStrategy.COCREATE, LinkBase.FOR_WEEKS)
    sql2linker.run(LinkStrategy.COCHANGE, LinkBase.FOR_WEEKS)


if __name__ == '__main__':
    path_to_comp0110 = os.path.expanduser('~/Project/PycharmProjects/comp0110')
    DataMiner(
        f'{path_to_comp0110}/.tmp',
        f'{path_to_comp0110}/example_repositories/guava'
    ).mining()
