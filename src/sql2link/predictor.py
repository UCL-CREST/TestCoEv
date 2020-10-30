from enum import Enum
from typing import Optional, Dict

from sql2link.establisher import *
from sql2link.establisher.for_commits.co_changed import (
    CoChangedInCommitClassLevelLinkEstablisher,
)
from sql2link.establisher.for_commits.with_filter import (
    CoChangedtedForSeparateChangeTypeFilteredCommitLinkEstablisher,
    CoChangedtedForAllChangeTypeFilteredCommitLinkEstablisher,
    CoCreatedWithFilteredCommitLinkEstablisher,
    AprioriWithFilteredCommitLinkEstablisher,
    CoChangedInCommitClassLevelLinkEstablisherWithFilter,
)
from sql2link.establisher.for_weeks.with_filter import (
    CoChangedtedForAllChangeTypeFilteredWeekLinkEstablisher,
    CoChangedtedForSeparateChangeTypeFilteredWeekLinkEstablisher,
)


class LinkStrategy(Enum):
    COCHANGE = "co_changed"
    COCREATE = "co_created"
    APRIORI = "apriori"


class LinkBase(Enum):
    FOR_COMMITS = "for_commits"
    FOR_WEEKS = "for_weeks"


class TraceabilityPredictor(object):
    def __init__(self, db_path: str):
        self.__db_path = db_path

    def run(
        self,
        strategy: LinkStrategy,
        base: LinkBase,
        parameters=None,
        is_previous_ignored: bool = False,
    ):
        if parameters is None:
            parameters = dict()
        establish: Optional[AbsLinkEstablisher] = None
        if strategy is LinkStrategy.COCREATE:
            if base is LinkBase.FOR_COMMITS:
                establish = CoCreatedInCommitLinkEstablisher(self.__db_path)
            elif base is LinkBase.FOR_WEEKS:
                establish = CoCreatedInWeekLinkEstablisher(self.__db_path)
        elif strategy is LinkStrategy.COCHANGE:
            if base is LinkBase.FOR_COMMITS:
                establish = CoChangedInCommitLinkEstablisher(self.__db_path)
            elif base is LinkBase.FOR_WEEKS:
                establish = CoChangedInWeekLinkEstablisher(self.__db_path)
        elif strategy is LinkStrategy.APRIORI:
            if base is LinkBase.FOR_COMMITS:
                establish = AprioriInCommitLinkEstablisher(self.__db_path)
            elif base is LinkBase.FOR_WEEKS:
                establish = AprioriInWeekLinkEstablisher(self.__db_path)
        if establish is not None:
            establish.do(parameters=parameters, is_previous_ingored=is_previous_ignored)

    def run_with_filter(
        self,
        strategy: LinkStrategy,
        base: LinkBase,
        is_for_all: bool = False,
        is_previous_ignored: bool = False,
        parameters: Dict = None,
    ):
        if parameters is None:
            parameters = dict()
        establish: Optional[AbsLinkEstablisher] = None
        if strategy is LinkStrategy.COCREATE:
            establish = CoCreatedWithFilteredCommitLinkEstablisher(self.__db_path)
        elif strategy is LinkStrategy.COCHANGE:
            if base is LinkBase.FOR_COMMITS:
                if is_for_all:
                    establish = (
                        CoChangedtedForAllChangeTypeFilteredCommitLinkEstablisher(
                            self.__db_path
                        )
                    )
                else:
                    establish = (
                        CoChangedtedForSeparateChangeTypeFilteredCommitLinkEstablisher(
                            self.__db_path
                        )
                    )
            elif base is LinkBase.FOR_WEEKS:
                if is_for_all:
                    establish = CoChangedtedForAllChangeTypeFilteredWeekLinkEstablisher(
                        self.__db_path
                    )
                else:
                    establish = (
                        CoChangedtedForSeparateChangeTypeFilteredWeekLinkEstablisher(
                            self.__db_path
                        )
                    )
        elif strategy is LinkStrategy.APRIORI:
            establish = AprioriWithFilteredCommitLinkEstablisher(self.__db_path)
        if establish is not None:
            establish.do(parameters=parameters, is_previous_ingored=is_previous_ignored)
        return None

    def run_class_level(
        self,
        strategy: LinkStrategy,
        base: LinkBase,
        parameters=None,
        is_previous_ignored: bool = False,
    ) -> None:
        if parameters is None:
            parameters = dict()
        establisher = CoChangedInCommitClassLevelLinkEstablisher(self.__db_path)
        establisher.do(parameters=parameters, is_previous_ingored=is_previous_ignored)
        return None

    def run_class_level_with_filter(
        self,
        strategy: LinkStrategy,
        base: LinkBase,
        parameters=None,
        is_previous_ignored: bool = False,
    ) -> None:
        if parameters is None:
            parameters = dict()
        establisher = CoChangedInCommitClassLevelLinkEstablisherWithFilter(
            self.__db_path
        )
        establisher.do(parameters=parameters, is_previous_ingored=is_previous_ignored)
        return None
