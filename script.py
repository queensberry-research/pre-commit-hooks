#!/usr/bin/env -S uv run --script --prerelease=disallow
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "click>=8.3.1, <9",
#   "dycw-actions>=0.10.2,<1",
#   "dycw-utilities>=0.179.1, <1",
#   "rich>=14.2.0, <15",
#   "typed-settings[attrs,click]>=25.3.0, <26",
#   "pyright>=1.1.407, <2",
#   "pytest-xdist>=3.8.0, <4",
# ]
# ///
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import actions.logging
from actions.constants import PYPROJECT_TOML
from actions.pre_commit.conformalize_repo.lib import (
    add_ci_pull_request_yaml,
    add_ci_push_yaml,
)
from actions.pre_commit.utilities import (
    ensure_aot_contains,
    get_aot,
    get_table,
    yield_toml_doc,
)
from actions.utilities import LOADER
from click import command
from rich.pretty import pretty_repr
from tomlkit import table
from typed_settings import (
    Secret,
    click_options,
    load_settings,
    option,
    secret,
    settings,
)
from utilities.click import CONTEXT_SETTINGS
from utilities.logging import basic_config
from utilities.os import is_pytest
from utilities.text import strip_and_dedent

if TYPE_CHECKING:
    from collections.abc import MutableSet
    from pathlib import Path

    from tomlkit.items import Table


__version__ = "0.2.3"
LOGGER = getLogger(__name__)
API_PACKAGES_QRT_PYPI = "api/packages/qrt/pypi"


@settings
class Settings:
    ci__token_github: Secret[str] | None = secret(
        default=Secret("${{secrets.ACTION_TOKEN}}"),
        help="Set up CI with this GitHub token",
    )
    ci__pull_request__pre_commit: bool = option(
        default=False, help="Set up 'pull-request.yaml' pre-commit"
    )
    ci__pull_request__pre_commit__submodules: str | None = option(
        default=None, help="Set up CI 'pull-request.yaml' pre-commit with submodules"
    )
    ci__pull_request__pyright: bool = option(
        default=False, help="Set up 'pull-request.yaml' pyright"
    )
    ci__pull_request__pytest: bool = option(
        default=False, help="Set up 'pull-request.yaml' pytest"
    )
    ci__pull_request__pytest__all_versions: bool = option(
        default=False,
        help="Set up 'pull-request.yaml' pytest with the current version only",
    )
    ci__pull_request__pytest__sops_and_age: bool = option(
        default=False, help="Set up 'pull-request.yaml' pytest sops/age"
    )
    ci__pull_request__pytest__sops_age_key: Secret[str] | None = secret(
        default=Secret("${{secrets.SOPS_AGE_KEY}}"),
        help="Set up CI 'pull-request.yaml' pytest with this 'age' key for 'sops'",
    )
    ci__pull_request__ruff: bool = option(
        default=False, help="Set up 'pull-request.yaml' ruff"
    )
    ci__push__pypi: bool = option(default=False, help="Set up 'push.yaml' with 'pypi'")
    ci__push__tag: bool = option(default=False, help="Set up 'push.yaml' tagging")
    gitea_host: str = option(default="gitea.main", help="Gitea host")
    gitea_port: int = option(default=3000, help="Gitea port")
    pypi__username: str = option(default="qrt-bot", help="PyPI user name")
    pypi__read_token: Secret[str] = secret(
        default=Secret("e43d1df41a3ecf96e4adbaf04e98cfaf094d253e"),
        help="PyPI read-only token",
    )
    pypi__read_write_token: Secret[str] = secret(
        default=Secret("${{secrets.ACTION_UV_PUBLISH_PASSWORD}}"),
        help="PyPI read/write token",
    )
    pyproject: bool = option(default=False, help="Set up 'pyproject.toml'")
    pytest__timeout: int | None = option(
        default=None, help="Set up 'pytest.toml' timeout"
    )
    python_version: str = option(default="3.13", help="Python version")
    repo_name: str | None = option(default=None, help="Repo name")
    script: str | None = option(
        default=None, help="Set up a script instead of a package"
    )

    @property
    def ci__push__publish__publish_url(self) -> Secret[str]:
        return Secret(f"https://{self.gitea_host_port}/{API_PACKAGES_QRT_PYPI}")

    @property
    def gitea_host_port(self) -> str:
        return f"{self.gitea_host}:{self.gitea_port}"


SETTINGS = load_settings(Settings, [LOADER])


##


@command(**CONTEXT_SETTINGS)
@click_options(Settings, [LOADER], show_envvars_in_help=True)
def main(settings: Settings, /) -> None:
    if is_pytest():
        return
    basic_config(obj=LOGGER)
    basic_config(obj=actions.logging.LOGGER)
    LOGGER.info(
        strip_and_dedent("""
            Running 'conformalize' (version %s) with settings:
            %s
        """),
        __version__,
        pretty_repr(settings),
    )
    modifications: set[Path] = set()
    if (
        settings.ci__pull_request__pre_commit
        or settings.ci__pull_request__pre_commit__submodules
        or settings.ci__pull_request__pyright
        or settings.ci__pull_request__pytest
        or settings.ci__pull_request__pytest__all_versions
        or settings.ci__pull_request__pytest__sops_and_age
        or settings.ci__pull_request__ruff
    ):
        add_ci_pull_request_yaml(
            gitea=True,
            modifications=modifications,
            certificates=True,
            pre_commit=settings.ci__pull_request__pre_commit,
            pre_commit__submodules=settings.ci__pull_request__pre_commit__submodules,
            pyright=settings.ci__pull_request__pyright,
            pytest__ubuntu=settings.ci__pull_request__pytest,
            pytest__all_versions=settings.ci__pull_request__pytest__all_versions,
            pytest__sops_age_key=settings.ci__pull_request__pytest__sops_age_key
            if settings.ci__pull_request__pytest__sops_and_age
            else None,
            pytest__timeout=settings.pytest__timeout,
            python_version=settings.python_version,
            repo_name=settings.repo_name,
            ruff=settings.ci__pull_request__ruff,
            script=settings.script,
            token_github=settings.ci__token_github,
            uv__native_tls=True,
        )
    if settings.ci__push__pypi or settings.ci__push__tag:
        add_ci_push_yaml(
            gitea=True,
            modifications=modifications,
            certificates=True,
            publish=settings.ci__push__pypi,
            publish__username=settings.pypi__username,
            publish__password=settings.pypi__read_write_token,
            publish__publish_url=settings.ci__push__publish__publish_url,
            tag=settings.ci__push__tag,
            token_github=settings.ci__token_github,
            uv__native_tls=True,
        )
    if settings.pyproject:
        add_pyproject_toml(
            modifications=modifications,
            gitea_host_port=settings.gitea_host_port,
            pypi__username=settings.pypi__username,
            pypi__read_token=settings.pypi__read_token,
        )


##


def add_pyproject_toml(
    *,
    modifications: MutableSet[Path] | None = None,
    gitea_host_port: str = SETTINGS.gitea_host_port,
    pypi__username: str = SETTINGS.pypi__username,
    pypi__read_token: Secret[str] = SETTINGS.pypi__read_token,
) -> None:
    with yield_toml_doc(PYPROJECT_TOML, modifications=modifications) as doc:
        tool = get_table(doc, "tool")
        uv = get_table(tool, "uv")
        index = get_aot(uv, "index")
        ensure_aot_contains(
            index,
            _add_pyproject_toml_index(
                host_port=gitea_host_port,
                username=pypi__username,
                password=pypi__read_token,
            ),
        )


def _add_pyproject_toml_index(
    *,
    host_port: str = SETTINGS.gitea_host_port,
    username: str = SETTINGS.pypi__username,
    password: Secret[str] = SETTINGS.pypi__read_token,
) -> Table:
    tab = table()
    tab["explicit"] = True
    tab["name"] = "gitea"
    tab["url"] = (
        f"https://{username}:{password.get_secret_value()}@{host_port}/{API_PACKAGES_QRT_PYPI}/simple"
    )
    return tab


if __name__ == "__main__":
    main()
