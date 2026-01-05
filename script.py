#!/usr/bin/env -S uv run --script --prerelease=disallow
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "click >=8.3.1, <9",
#   "dycw-actions>=0.3.40, <1",
#   "dycw-conformalize >=0.13.6, <1",
#   "dycw-utilities >=0.175.36, <1",
#   "rich >=14.2.0, <15",
#   "typed-settings[attrs, click] >=25.3.0, <26",
#   "pyright >=1.1.407, <2",
#   "pytest-xdist >=3.8.0, <4",
# ]
# ///
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import conformalize.logging
from actions.conformalize.dicts import (
    run_action_pre_commit_dict,
    run_action_publish_dict,
    run_action_pyright_dict,
    run_action_pytest_dict,
    run_action_ruff_dict,
    run_action_tag_dict,
)
from click import command
from conformalize.constants import PYPROJECT_TOML
from conformalize.lib import (
    ensure_aot_contains,
    ensure_contains,
    get_aot,
    get_dict,
    get_list,
    get_table,
    yield_python_versions,
    yield_toml_doc,
    yield_yaml_dict,
)
from conformalize.settings import LOADER
from rich.pretty import pretty_repr
from ruamel.yaml.scalarstring import LiteralScalarString
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

    from conformalize.types import StrDict
    from tomlkit.items import Table


__version__ = "0.1.28"
LOGGER = getLogger(__name__)
API_PACKAGES_QRT_PYPI = "api/packages/qrt/pypi"
SECRETS_ACTION_TOKEN = "${{secrets.ACTION_TOKEN}}"  # noqa: S105


@settings
class Settings:
    gitea_host: str = option(default="gitea.main", help="Gitea host")
    gitea_port: int = option(default=3000, help="Gitea port")
    gitea_pypi_username: str = option(
        default="qrt-bot", help="Gitea PyPI publish username"
    )
    gitea_pypi_token: Secret[str] = secret(
        default=Secret("e43d1df41a3ecf96e4adbaf04e98cfaf094d253e"),
        help="Gitea PyPI publish token",
    )
    gitea__pull_request__pre_commit: bool = option(
        default=False, help="Set up 'pull-request.yaml' pre-commit"
    )
    gitea__pull_request__pre_commit__submodules: str | None = option(
        default=None, help="Set up 'pull-request.yaml' pre-commit with submodules"
    )
    gitea__pull_request__pyright: bool = option(
        default=False, help="Set up 'pull-request.yaml' pyright"
    )
    gitea__pull_request__pytest: bool = option(
        default=False, help="Set up 'pull-request.yaml' pytest"
    )
    gitea__pull_request__ruff: bool = option(
        default=False, help="Set up 'pull-request.yaml' ruff"
    )
    gitea__push__docker: bool = option(
        default=False, help="Set up 'push.yaml' with 'docker'"
    )
    gitea__push__pypi: bool = option(
        default=False, help="Set up 'push.yaml' with 'pypi'"
    )
    gitea__push__tag: bool = option(default=False, help="Set up 'push.yaml' with 'tag'")
    pyproject: bool = option(default=False, help="Set up 'pyproject.toml'")
    pytest__timeout: int | None = option(
        default=None, help="Set up 'pytest.toml' timeout"
    )
    python_version: str = option(default="3.13", help="Python version")
    script: str | None = option(
        default=None, help="Set up a script instead of a package"
    )

    @property
    def gitea_host_port(self) -> str:
        return f"{self.gitea_host}:{self.gitea_port}"


SETTINGS = load_settings(Settings, [LOADER])


##


@command(**CONTEXT_SETTINGS)
@click_options(Settings, "app", show_envvars_in_help=True)
def main(settings: Settings, /) -> None:
    if is_pytest():
        return
    basic_config(obj=__name__)
    basic_config(obj=conformalize.logging.LOGGER)
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
        settings.gitea__pull_request__pre_commit
        or settings.gitea__pull_request__pre_commit__submodules
        or settings.gitea__pull_request__pyright
        or settings.gitea__pull_request__pytest
        or settings.gitea__pull_request__ruff
    ):
        add_gitea_pull_request_yaml(
            modifications=modifications,
            pre_commit=settings.gitea__pull_request__pre_commit,
            pre_commit__submodules=settings.gitea__pull_request__pre_commit__submodules,
            pyright=settings.gitea__pull_request__pyright,
            pytest=settings.gitea__pull_request__pytest,
            pytest__timeout=settings.pytest__timeout,
            ruff=settings.gitea__pull_request__ruff,
            python_version=settings.python_version,
            script=settings.script,
        )
    if (
        settings.gitea__push__docker
        or settings.gitea__push__pypi
        or settings.gitea__push__tag
    ):
        add_gitea_push_yaml(
            modifications=modifications,
            docker=settings.gitea__push__docker,
            pypi=settings.gitea__push__pypi,
            tag=settings.gitea__push__tag,
            gitea_host_port=settings.gitea_host_port,
        )
    if settings.pyproject:
        add_pyproject_toml(
            modifications=modifications,
            gitea_host_port=settings.gitea_host_port,
            gitea_pypi_username=settings.gitea_pypi_username,
            gitea_pypi_token=settings.gitea_pypi_token,
        )


##


def add_gitea_pull_request_yaml(
    *,
    modifications: MutableSet[Path] | None = None,
    pre_commit: bool = SETTINGS.gitea__pull_request__pre_commit,
    pre_commit__submodules: str
    | None = SETTINGS.gitea__pull_request__pre_commit__submodules,
    pyright: bool = SETTINGS.gitea__pull_request__pyright,
    pytest: bool = SETTINGS.gitea__pull_request__pytest,
    pytest__timeout: int | None = SETTINGS.pytest__timeout,
    ruff: bool = SETTINGS.gitea__pull_request__ruff,
    python_version: str = SETTINGS.python_version,
    script: str | None = SETTINGS.script,
) -> None:
    with yield_yaml_dict(
        ".gitea/workflows/pull-request.yaml", modifications=modifications
    ) as dict_:
        dict_["name"] = "pull-request"
        on = get_dict(dict_, "on")
        pull_request = get_dict(on, "pull_request")
        branches = get_list(pull_request, "branches")
        ensure_contains(branches, "master")
        schedule = get_list(on, "schedule")
        ensure_contains(schedule, {"cron": "0 0 * * *"})
        jobs = get_dict(dict_, "jobs")
        if pre_commit or pre_commit__submodules:
            pre_commit_dict = get_dict(jobs, "pre-commit")
            pre_commit_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(pre_commit_dict, "steps")
            ensure_contains(
                steps,
                random_sleep("pre-commit"),
                update_ca_certificates("pre-commit"),
                run_action_pre_commit_dict(
                    token_uv=SECRETS_ACTION_TOKEN,
                    submodules=pre_commit__submodules,
                    repos=LiteralScalarString(
                        strip_and_dedent("""
                            dycw/conformalize
                            qrt-public/conformalize
                            pre-commit/pre-commit-hooks
                        """)
                    ),
                ),
            )
        if pyright:
            pyright_dict = get_dict(jobs, "pyright")
            pyright_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(pyright_dict, "steps")
            ensure_contains(
                steps,
                random_sleep("pyright"),
                update_ca_certificates("pyright"),
                run_action_pyright_dict(
                    token_uv=SECRETS_ACTION_TOKEN,
                    python_version=python_version,
                    native_tls=True,
                    with_requirements=script,
                ),
            )
        if pytest:
            pytest_dict = get_dict(jobs, "pytest")
            env = get_dict(pytest_dict, "env")
            env["CI"] = "1"
            pytest_dict["name"] = (
                "pytest (${{matrix.os}}, ${{matrix.python-version}}, ${{matrix.resolution}})"
            )
            pytest_dict["runs-on"] = "${{matrix.os}}"
            steps = get_list(pytest_dict, "steps")
            ensure_contains(
                steps,
                random_sleep("pytest"),
                update_ca_certificates("pytest"),
                run_action_pytest_dict(
                    token_uv=SECRETS_ACTION_TOKEN,
                    python_version="${{matrix.python-version}}",
                    resolution="${{matrix.resolution}}",
                    native_tls=True,
                    with_requirements=script,
                ),
            )
            strategy_dict = get_dict(pytest_dict, "strategy")
            strategy_dict["fail-fast"] = False
            matrix = get_dict(strategy_dict, "matrix")
            os = get_list(matrix, "os")
            ensure_contains(os, "ubuntu-latest")
            python_version_dict = get_list(matrix, "python-version")
            ensure_contains(python_version_dict, *yield_python_versions(python_version))
            resolution = get_list(matrix, "resolution")
            ensure_contains(resolution, "highest", "lowest-direct")
            if pytest__timeout is not None:
                pytest_dict["timeout-minutes"] = max(round(pytest__timeout / 60), 1)
        if ruff:
            ruff_dict = get_dict(jobs, "ruff")
            ruff_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(ruff_dict, "steps")
            ensure_contains(
                steps,
                random_sleep("ruff"),
                update_ca_certificates("ruff"),
                run_action_ruff_dict(token_ruff=SECRETS_ACTION_TOKEN),
            )


##


def add_gitea_push_yaml(
    *,
    modifications: MutableSet[Path] | None = None,
    docker: bool = SETTINGS.gitea__push__docker,
    pypi: bool = SETTINGS.gitea__push__pypi,
    tag: bool = SETTINGS.gitea__push__tag,
    gitea_host_port: str = SETTINGS.gitea_host_port,
) -> None:
    with yield_yaml_dict(
        ".gitea/workflows/push.yaml", modifications=modifications
    ) as dict_:
        dict_["name"] = "push"
        on = get_dict(dict_, "on")
        push = get_dict(on, "push")
        branches = get_list(push, "branches")
        ensure_contains(branches, "master")
        jobs = get_dict(dict_, "jobs")
        if docker:
            raise NotImplementedError
        if tag:
            tag_dict = get_dict(jobs, "tag")
            tag_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(tag_dict, "steps")
            ensure_contains(
                steps,
                update_ca_certificates("tag"),
                run_action_tag_dict(token_uv=SECRETS_ACTION_TOKEN),
            )
        if pypi:
            pypi_dict = get_dict(jobs, "pypi")
            pypi_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(pypi_dict, "steps")
            ensure_contains(
                steps,
                update_ca_certificates("pypi"),
                run_action_publish_dict(
                    token_uv=SECRETS_ACTION_TOKEN,
                    username="qrt-bot",
                    password="${{secrets.ACTION_UV_PUBLISH_PASSWORD}}",  # noqa: S106
                    publish_url=f"https://{gitea_host_port}/{API_PACKAGES_QRT_PYPI}",
                    native_tls=True,
                ),
            )


##


def add_pyproject_toml(
    *,
    modifications: MutableSet[Path] | None = None,
    gitea_host_port: str = SETTINGS.gitea_host_port,
    gitea_pypi_username: str = SETTINGS.gitea_pypi_username,
    gitea_pypi_token: Secret[str] = SETTINGS.gitea_pypi_token,
) -> None:
    with yield_toml_doc(PYPROJECT_TOML, modifications=modifications) as doc:
        tool = get_table(doc, "tool")
        uv = get_table(tool, "uv")
        index = get_aot(uv, "index")
        ensure_aot_contains(
            index,
            _add_pyproject_toml_index(
                gitea_host_port=gitea_host_port,
                gitea_pypi_username=gitea_pypi_username,
                gitea_pypi_token=gitea_pypi_token,
            ),
        )


def _add_pyproject_toml_index(
    *,
    gitea_host_port: str = SETTINGS.gitea_host_port,
    gitea_pypi_username: str = SETTINGS.gitea_pypi_username,
    gitea_pypi_token: Secret[str] = SETTINGS.gitea_pypi_token,
) -> Table:
    tab = table()
    tab["explicit"] = True
    tab["name"] = "gitea"
    tab["url"] = (
        f"https://{gitea_pypi_username}:{gitea_pypi_token.get_secret_value()}@{gitea_host_port}/{API_PACKAGES_QRT_PYPI}/simple"
    )
    return tab


##


def random_sleep(desc: str, /) -> StrDict:
    return {
        "if": "gitea.event_name == 'schedule'",
        "name": f"Random sleep with logging ({desc})",
        "uses": "dycw/action-random-sleep@latest",
        "with": {"max": 3600, "step": 60},
    }


def update_ca_certificates(desc: str, /) -> StrDict:
    return {
        "name": f"Update CA certificates ({desc})",
        "run": "sudo update-ca-certificates",
    }


if __name__ == "__main__":
    main()
