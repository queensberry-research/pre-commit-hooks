#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "click >=8.3.1, <8.4",
#   "dycw-conformalize >=0.11.4, <0.12",
#   "dycw-utilities >=0.175.36, <0.176",
#   "rich >=14.2.0, <14.3",
#   "typed-settings[attrs, click] >=25.3.0, <25.4",
#   "pyright",
#   "pytest-xdist",
# ]
# ///
from __future__ import annotations

from logging import getLogger
from typing import TYPE_CHECKING

import conformalize.logging
from click import command
from conformalize.lib import (
    ensure_contains,
    get_dict,
    get_list,
    run_action_pre_commit_dict,
    run_action_publish_dict,
    run_action_pyright_dict,
    run_action_pytest_dict,
    run_action_ruff_dict,
    run_action_tag_dict,
    yield_yaml_dict,
)
from conformalize.settings import LOADER
from rich.pretty import pretty_repr
from typed_settings import click_options, load_settings, option, settings
from utilities.click import CONTEXT_SETTINGS
from utilities.logging import basic_config
from utilities.os import is_pytest
from utilities.text import strip_and_dedent

if TYPE_CHECKING:
    from collections.abc import MutableSet
    from pathlib import Path

__version__ = "0.1.11"
LOGGER = getLogger(__name__)
UPDATE_CA_CERTIFICATES = {
    "name": "Update CA certificates",
    "run": "sudo update-ca-certificates",
}


@settings
class Settings:
    gitea_host: str = option(default="gitea.main", help="Gitea host")
    gitea__pull_request__pre_commit: bool = option(
        default=False, help="Set up 'pull-request.yaml' pre-commit"
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
    pytest__timeout: int | None = option(
        default=None, help="Set up 'pytest.toml' timeout"
    )
    python_version: str = option(default="3.13", help="Python version")


SETTINGS = load_settings(Settings, [LOADER])


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
        or settings.gitea__pull_request__pyright
        or settings.gitea__pull_request__pytest
        or settings.gitea__pull_request__ruff
    ):
        add_gitea_pull_request_yaml(
            modifications=modifications,
            pre_commit=settings.gitea__pull_request__pre_commit,
            pyright=settings.gitea__pull_request__pyright,
            pytest=settings.gitea__pull_request__pytest,
            pytest__timeout=settings.pytest__timeout,
            ruff=settings.gitea__pull_request__ruff,
            python_version=settings.python_version,
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
            gitea_host=settings.gitea_host,
        )


def add_gitea_pull_request_yaml(
    *,
    modifications: MutableSet[Path] | None = None,
    pre_commit: bool = SETTINGS.gitea__pull_request__pre_commit,
    pyright: bool = SETTINGS.gitea__pull_request__pyright,
    pytest: bool = SETTINGS.gitea__pull_request__pytest,
    pytest__timeout: int | None = SETTINGS.pytest__timeout,
    ruff: bool = SETTINGS.gitea__pull_request__ruff,
    python_version: str = SETTINGS.python_version,
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
        if pre_commit:
            pre_commit_dict = get_dict(jobs, "pre-commit")
            pre_commit_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(pre_commit_dict, "steps")
            ensure_contains(steps, UPDATE_CA_CERTIFICATES, run_action_pre_commit_dict())
        if pyright:
            pyright_dict = get_dict(jobs, "pyright")
            pyright_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(pyright_dict, "steps")
            ensure_contains(
                steps,
                UPDATE_CA_CERTIFICATES,
                run_action_pyright_dict(python_version=python_version),
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
            ensure_contains(steps, UPDATE_CA_CERTIFICATES, run_action_pytest_dict())
            strategy_dict = get_dict(pytest_dict, "strategy")
            strategy_dict["fail-fast"] = False
            matrix = get_dict(strategy_dict, "matrix")
            os = get_list(matrix, "os")
            ensure_contains(os, "macos-latest", "ubuntu-latest")
            python_version_dict = get_list(matrix, "python-version")
            ensure_contains(python_version_dict, "3.13", "3.14")
            resolution = get_list(matrix, "resolution")
            ensure_contains(resolution, "highest", "lowest-direct")
            if pytest__timeout is not None:
                pytest_dict["timeout-minutes"] = max(round(pytest__timeout / 60), 1)
        if ruff:
            ruff_dict = get_dict(jobs, "ruff")
            ruff_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(ruff_dict, "steps")
            ensure_contains(steps, UPDATE_CA_CERTIFICATES, run_action_ruff_dict())


def add_gitea_push_yaml(
    *,
    modifications: MutableSet[Path] | None = None,
    docker: bool = SETTINGS.gitea__push__docker,
    pypi: bool = SETTINGS.gitea__push__pypi,
    tag: bool = SETTINGS.gitea__push__tag,
    gitea_host: str = SETTINGS.gitea_host,
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
            ensure_contains(steps, UPDATE_CA_CERTIFICATES, run_action_tag_dict())
        if pypi:
            pypi_dict = get_dict(jobs, "pypi")
            pypi_dict["runs-on"] = "ubuntu-latest"
            steps = get_list(pypi_dict, "steps")
            ensure_contains(
                steps,
                UPDATE_CA_CERTIFICATES,
                run_action_publish_dict(
                    username="qrt-bot",
                    password="${{secrets.ACTION_UV_PUBLISH_PASSWORD}}",  # noqa: S106
                    publish_url=f"https://{gitea_host}:3000/api/packages/qrt/pypi/",
                    native_tls=True,
                ),
            )


if __name__ == "__main__":
    main()
