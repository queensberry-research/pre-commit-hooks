from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import GITEA_PUSH_YAML, paths_argument
from pre_commit_hooks.utilities import (
    add_update_certificates,
    ensure_contains_partial_dict,
    get_set_dict,
    get_set_list_dicts,
    merge_paths,
    run_all_maybe_raise,
    yield_yaml_dict,
)
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks._click import package_not_req_option
from qrt_pre_commit_hooks._constants import ACTION_TOKEN
from qrt_pre_commit_hooks._enums import Index, Package
from qrt_pre_commit_hooks._settings import SETTINGS
from qrt_pre_commit_hooks._utilities import yield_job_with

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike, StrDict


@command(**CONTEXT_SETTINGS)
@paths_argument
@package_not_req_option
def cli(*, paths: tuple[Path, ...], package: Package | None = None) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=GITEA_PUSH_YAML)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, package=package) for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = GITEA_PUSH_YAML, package: Package | None = None) -> bool:
    modifications: set[Path] = set()
    _modify_tag(path=path, modifications=modifications)
    if package is not None:
        _modify_publish(path=path, modifications=modifications)
    if package is Package.infra:
        _add_nanode(path=path, modifications=modifications)
    return len(modifications) == 0


def _modify_tag(
    *, path: PathLike = GITEA_PUSH_YAML, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_job_with(
        "tag",
        "Tag the latest commit",
        "dycw/action-tag-commit@latest",
        path=path,
        modifications=modifications,
    ) as dict_:
        dict_["token-github"] = ACTION_TOKEN


def _modify_publish(
    *, path: PathLike = GITEA_PUSH_YAML, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_job_with(
        "publish",
        "Build and publish the package",
        "dycw/action-publish-package@latest",
        path=path,
        modifications=modifications,
    ) as dict_:
        _add_dict(dict_, Index.gitea)


def _add_nanode(
    *, path: PathLike = GITEA_PUSH_YAML, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        publish_nanode = get_set_dict(jobs, "publish-nanode")
        publish_nanode["runs-on"] = "ubuntu-latest"
        steps = get_set_list_dicts(publish_nanode, "steps")
        add_update_certificates(steps)
        step = ensure_contains_partial_dict(
            steps,
            {
                "name": "Build and publish the package",
                "uses": "dycw/action-publish-package@latest",
            },
        )
        with_ = get_set_dict(step, "with")
        _add_dict(with_, Index.nanode)
        with_["native-tls"] = True


def _add_dict(dict_: StrDict, index: Index, /) -> None:
    dict_["token-github"] = ACTION_TOKEN
    dict_["username"] = SETTINGS.indexes.get_username(index)
    dict_["password"] = SETTINGS.indexes.get_publish_password(index, visible=False)
    dict_["publish-url"] = SETTINGS.indexes.get_publish_url(index)


if __name__ == "__main__":
    cli()
