from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from actions.constants import ACTIONS_URL, PRE_COMMIT_CONFIG_YAML
from actions.pre_commit.conformalize_repo.lib import (
    add_ci_pull_request_yaml,
    add_ci_push_yaml,
    get_tool_uv,
)
from actions.pre_commit.update_requirements.constants import UPDATE_REQUIREMENTS_SUB_CMD
from actions.pre_commit.utilities import (
    ensure_contains,
    get_list_dicts,
    get_partial_dict,
    get_set_aot,
    get_set_list_strs,
    yield_pyproject_toml,
    yield_yaml_dict,
)
from tomlkit import table
from typed_settings import Secret
from utilities.tabulate import func_param_desc
from utilities.text import repr_str

from conformalize import __version__
from conformalize.constants import (
    ACTION_TOKEN,
    API_PACKAGES_QRT_PYPI,
    PYPI_GITEA_READ_TOKEN,
    PYPI_GITEA_READ_WRITE_TOKEN,
    PYPI_GITEA_USERNAME,
    PYPI_NANODE_PASSWORD,
    PYPI_NANODE_USERNAME,
    SOPS_AGE_KEY,
)
from conformalize.logging import LOGGER
from conformalize.settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import MutableSet
    from pathlib import Path

    from tomlkit.items import Table


def conformalize(
    *,
    ci__pull_request__pre_commit: bool = SETTINGS.ci__pull_request__pre_commit,
    ci__pull_request__pre_commit__submodules: str
    | None = SETTINGS.ci__pull_request__pre_commit__submodules,
    ci__pull_request__pyright: bool = SETTINGS.ci__pull_request__pyright,
    ci__pull_request__pytest: bool = SETTINGS.ci__pull_request__pytest,
    ci__pull_request__pytest__all_versions: bool = SETTINGS.ci__pull_request__pytest__all_versions,
    ci__pull_request__pytest__sops_and_age: bool = SETTINGS.ci__pull_request__pytest__sops_and_age,
    ci__pull_request__ruff: bool = SETTINGS.ci__pull_request__ruff,
    ci__push__pypi__gitea: bool = SETTINGS.ci__push__pypi__gitea,
    ci__push__pypi__nanode: bool = SETTINGS.ci__push__pypi__nanode,
    ci__push__tag: bool = SETTINGS.ci__push__tag,
    gitea_host: str = SETTINGS.gitea_host,
    gitea_port: int = SETTINGS.gitea_port,
    pyproject: bool = SETTINGS.pyproject,
    pytest__timeout: int | None = SETTINGS.pytest__timeout,
    python_version: str = SETTINGS.python_version,
    repo_name: str | None = SETTINGS.repo_name,
    script: str | None = SETTINGS.script,
) -> None:
    LOGGER.info(
        func_param_desc(
            conformalize,
            __version__,
            f"{ci__pull_request__pre_commit=}",
            f"{ci__pull_request__pre_commit__submodules=}",
            f"{ci__pull_request__pyright=}",
            f"{ci__pull_request__pytest=}",
            f"{ci__pull_request__pytest__all_versions=}",
            f"{ci__pull_request__pytest__sops_and_age=}",
            f"{ci__pull_request__ruff=}",
            f"{ci__push__pypi__gitea=}",
            f"{ci__push__pypi__nanode=}",
            f"{ci__push__tag=}",
            f"{gitea_host=}",
            f"{gitea_port=}",
            f"{pyproject=}",
            f"{pytest__timeout=}",
            f"{python_version=}",
            f"{repo_name=}",
            f"{script=}",
        )
    )
    modifications: set[Path] = set()
    if (
        ci__pull_request__pre_commit
        or ci__pull_request__pyright
        or ci__pull_request__pytest
        or ci__pull_request__ruff
    ):
        add_ci_pull_request_yaml(
            gitea=True,
            modifications=modifications,
            certificates=True,
            pre_commit=ci__pull_request__pre_commit,
            pre_commit__submodules=ci__pull_request__pre_commit__submodules,
            pyright=ci__pull_request__pyright,
            pytest__ubuntu=ci__pull_request__pytest,
            pytest__all_versions=ci__pull_request__pytest__all_versions,
            pytest__sops_age_key=Secret(SOPS_AGE_KEY)
            if ci__pull_request__pytest__sops_and_age
            else None,
            pytest__timeout=pytest__timeout,
            python_version=python_version,
            repo_name=repo_name,
            ruff=ci__pull_request__ruff,
            script=script,
            token_github=Secret(ACTION_TOKEN),
            uv__native_tls=True,
        )
    if ci__push__pypi__gitea or ci__push__pypi__nanode or ci__push__tag:
        add_ci_push_yaml(
            gitea=True,
            modifications=modifications,
            certificates=True,
            publish__primary=ci__push__pypi__gitea,
            publish__primary__job_name="gitea",
            publish__primary__username=PYPI_GITEA_USERNAME,
            publish__primary__password=Secret(PYPI_GITEA_READ_WRITE_TOKEN),
            publish__primary__publish_url=f"https://{gitea_host}:{gitea_port}/{API_PACKAGES_QRT_PYPI}",
            publish__secondary=ci__push__pypi__nanode,
            publish__secondary__job_name="nanode",
            publish__secondary__username=PYPI_NANODE_USERNAME,
            publish__secondary__password=Secret(PYPI_NANODE_PASSWORD),
            publish__secondary__publish_url="https://pypi.queensberryresearch.com",
            tag=ci__push__tag,
            token_github=Secret(ACTION_TOKEN),
            uv__native_tls=True,
        )
    if pyproject:
        add_pyproject_toml(
            modifications=modifications, host=gitea_host, port=gitea_port
        )
        add_update_requirements_index(
            modifications=modifications, host=gitea_host, port=gitea_port
        )
    if len(modifications) >= 1:
        LOGGER.info(
            "Exiting due to modifications: %s",
            ", ".join(map(repr_str, sorted(modifications))),
        )
        sys.exit(1)


##


def add_pyproject_toml(
    *,
    modifications: MutableSet[Path] | None = None,
    host: str = SETTINGS.gitea_host,
    port: int = SETTINGS.gitea_port,
) -> None:
    with yield_pyproject_toml(modifications=modifications) as doc:
        uv = get_tool_uv(doc)
        index = get_set_aot(uv, "index")
        ensure_contains(index, _add_pyproject_toml_index(host=host, port=port))


def _add_pyproject_toml_index(
    *, host: str = SETTINGS.gitea_host, port: int = SETTINGS.gitea_port
) -> Table:
    tab = table()
    tab["explicit"] = True
    tab["name"] = "gitea"
    tab["url"] = _pypi_gitea_url(host=host, port=port)
    return tab


##


def add_update_requirements_index(
    *,
    modifications: MutableSet[Path] | None = None,
    host: str = SETTINGS.gitea_host,
    port: int = SETTINGS.gitea_port,
) -> None:
    with yield_yaml_dict(PRE_COMMIT_CONFIG_YAML, modifications=modifications) as dict_:
        try:
            repos_list = get_list_dicts(dict_, "repos")
            repo_dict = get_partial_dict(repos_list, {"repo": ACTIONS_URL})
            hooks_list = get_list_dicts(repo_dict, "hooks")
            hook_dict = get_partial_dict(
                hooks_list, {"id": UPDATE_REQUIREMENTS_SUB_CMD}
            )
        except KeyError:
            return
        args_dict = get_set_list_strs(hook_dict, "args")
        url = _pypi_gitea_url(host=host, port=port)
        ensure_contains(args_dict, f"--indexes={url}")


##


def _pypi_gitea_url(
    *, host: str = SETTINGS.gitea_host, port: int = SETTINGS.gitea_port
) -> str:
    return f"https://{PYPI_GITEA_USERNAME}:{PYPI_GITEA_READ_TOKEN}@{host}:{port}/{API_PACKAGES_QRT_PYPI}/simple"


__all__ = ["add_pyproject_toml", "add_update_requirements_index", "conformalize"]
