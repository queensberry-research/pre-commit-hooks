from __future__ import annotations

from enum import StrEnum, unique
from typing import assert_never


@unique
class Index(StrEnum):
    gitea = "gitea"
    nanode = "nanode"

    @property
    def package(self) -> Package:
        match self:
            case Index.gitea:
                return Package.trading
            case Index.nanode:
                return Package.infra
            case never:
                assert_never(never)


@unique
class Package(StrEnum):
    trading = "trading"
    infra = "infra"

    @property
    def pkg_index(self) -> Index:
        match self:
            case Package.trading:
                return Index.gitea
            case Package.infra:
                return Index.nanode
            case never:
                assert_never(never)


__all__ = ["Index", "Package"]
