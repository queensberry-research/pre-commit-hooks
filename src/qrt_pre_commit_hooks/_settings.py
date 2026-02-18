# ruff: noqa: TC002, TC003
from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, assert_never

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from utilities.core import substitute
from utilities.importlib import files
from utilities.pydantic_settings import (
    CustomBaseSettings,
    PathLikeOrWithSection,
    load_settings,
)
from utilities.types import SecretLike

from qrt_pre_commit_hooks._constants import (
    PYPI_GITEA_READ_TOKEN,
    PYPI_GITEA_READ_WRITE_TOKEN,
    PYPI_NANODE_PASSWORD,
)
from qrt_pre_commit_hooks._enums import Index, Package

_FILES = files(anchor="qrt_pre_commit_hooks")
_SETTINGS_TOML = "settings.toml"


class _Settings(CustomBaseSettings):
    toml_files: ClassVar[Sequence[PathLikeOrWithSection]] = [
        (_SETTINGS_TOML, "qrt_pre_commit_hooks"),
        _FILES.joinpath(_SETTINGS_TOML),
    ]

    gitea: _GiteaSettings
    indexes: _IndexesSettings
    packages: list[_Package1Settings]
    url: str


class _GiteaSettings(BaseSettings):
    host: str
    port: int
    owner: str


class _IndexesSettings(BaseSettings):
    gitea: _IndexesGiteaSettings
    nanode: _IndexesNanodeSettings

    def url(self, index: Index, /) -> str:
        match index:
            case Index.gitea:
                return self.gitea.url
            case Index.nanode:
                return self.nanode.url
            case never:
                assert_never(never)

    def username(self, index: Index, /) -> str:
        match index:
            case Index.gitea:
                return self.gitea.username
            case Index.nanode:
                return self.nanode.username
            case never:
                assert_never(never)

    def password(
        self, index: Index, /, *, write: bool = False, ci: bool = False
    ) -> SecretLike:
        match index, write, ci:
            case Index.gitea, False, False:
                return self.gitea.passwords.read
            case Index.gitea, False, True:
                return PYPI_GITEA_READ_TOKEN
            case Index.gitea, True, False:
                return self.gitea.passwords.write
            case Index.gitea, True, True:
                return PYPI_GITEA_READ_WRITE_TOKEN
            case Index.nanode, _, False:
                return self.nanode.password
            case Index.nanode, _, True:
                return PYPI_NANODE_PASSWORD
            case never:
                assert_never(never)


class _IndexesGiteaSettings(BaseSettings):
    url_tmpl: str
    username: str
    passwords: _IndexesGiteaPasswordsSettings

    @property
    def url(self) -> str:
        return substitute(
            self.url_tmpl,
            host=SETTINGS.gitea.host,
            port=SETTINGS.gitea.port,
            owner=SETTINGS.gitea.owner,
        )


class _IndexesGiteaPasswordsSettings(BaseSettings):
    read: SecretStr
    write: SecretStr


class _IndexesNanodeSettings(BaseSettings):
    url: str
    username: str
    password: SecretStr


class _Package1Settings(BaseSettings):
    name: str
    type: Package


SETTINGS = load_settings(_Settings)


__all__ = ["SETTINGS"]
