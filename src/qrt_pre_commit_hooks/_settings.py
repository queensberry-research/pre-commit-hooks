# ruff: noqa: TC002, TC003
from __future__ import annotations

from collections.abc import Sequence
from typing import ClassVar, assert_never

from pydantic import SecretStr
from pydantic_settings import BaseSettings
from utilities.core import extract_group
from utilities.importlib import files
from utilities.pydantic_settings import (
    CustomBaseSettings,
    PathLikeOrWithSection,
    load_settings,
)

from qrt_pre_commit_hooks._enums import Index, Package

_FILES = files(anchor="qrt_pre_commit_hooks")
_SETTINGS_TOML = "settings.toml"


class _Settings(CustomBaseSettings):
    toml_files: ClassVar[Sequence[PathLikeOrWithSection]] = [
        (_SETTINGS_TOML, "qrt_pre_commit_hooks"),
        _FILES.joinpath(_SETTINGS_TOML),
    ]

    indexes: _IndexesSettings
    packages: list[_Package1Settings]
    url: str


class _IndexesSettings(BaseSettings):
    gitea: _IndexesGiteaSettings
    nanode: _IndexesNanodeSettings

    def get_publish_url(self, index: Index, /) -> str:
        return self._get_index(index).publish_url

    def get_read_password(self, index: Index, /, *, visible: bool) -> str:
        match index, visible:
            case Index.gitea, False:
                return "${{secrets.PYPI_GITEA_READ_TOKEN}}"
            case Index.gitea, True:
                return self.gitea.passwords.read.get_secret_value()
            case Index.nanode, False:
                return "${{secrets.PYPI_NANODE_PASSWORD}}"
            case Index.nanode, True:
                return self.nanode.password.get_secret_value()
            case never:
                assert_never(never)

    def get_publish_password(self, index: Index, /, *, visible: bool) -> str:
        match index, visible:
            case Index.gitea, False:
                return "${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}"
            case Index.gitea, True:
                return self.gitea.passwords.publish.get_secret_value()
            case Index.nanode, False:
                return "${{secrets.PYPI_NANODE_PASSWORD}}"
            case Index.nanode, True:
                return self.nanode.password.get_secret_value()
            case never:
                assert_never(never)

    def get_read_url(self, index: Index, /, *, visible: bool | None = None) -> str:
        return self._get_index(index).read_url(visible=visible)

    def get_username(self, index: Index, /) -> str:
        return self._get_index(index).username

    def _get_index(
        self, index: Index, /
    ) -> _IndexesGiteaSettings | _IndexesNanodeSettings:
        match index:
            case Index.gitea:
                return self.gitea
            case Index.nanode:
                return self.nanode
            case never:
                assert_never(never)


class _IndexesGiteaSettings(BaseSettings):
    publish_url: str
    username: str
    passwords: _IndexesGiteaPasswordsSettings

    def read_url(self, *, visible: bool | None = None) -> str:
        return _read_url(self, Package.trading, visible=visible)


class _IndexesGiteaPasswordsSettings(BaseSettings):
    read: SecretStr
    publish: SecretStr


class _IndexesNanodeSettings(BaseSettings):
    publish_url: str
    username: str
    password: SecretStr

    def read_url(self, *, visible: bool | None = None) -> str:
        return _read_url(self, Package.infra, visible=visible)


class _Package1Settings(BaseSettings):
    name: str
    type: Package


SETTINGS = load_settings(_Settings)


def _read_url(
    obj: _IndexesGiteaSettings | _IndexesNanodeSettings,
    package: Package,
    /,
    *,
    visible: bool | None = None,
) -> str:
    base = extract_group(r"^https://([\w\.\/\:]+)$", obj.publish_url)
    if visible is None:
        middle = base
    else:
        password = SETTINGS.indexes.get_read_password(
            package.pkg_index, visible=visible
        )
        middle = f"{obj.username}:{password}@{base}"
    return f"https://{middle}/simple"


__all__ = ["SETTINGS"]
