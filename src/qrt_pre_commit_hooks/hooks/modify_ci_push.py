from __future__ import annotations

from functools import partial
from pathlib import Path
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
from utilities.os import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks.constants import (
    ACTION_TOKEN,
    PYPI_GITEA_PUBLISH_URL,
    PYPI_GITEA_READ_WRITE_TOKEN,
    PYPI_GITEA_USERNAME,
    PYPI_NANODE_PASSWORD,
    PYPI_NANODE_PUBLISH_URL,
    PYPI_NANODE_USERNAME,
    ci_nanode_option,
)
from qrt_pre_commit_hooks.utilities import yield_job_with

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@ci_nanode_option
def _main(*, paths: tuple[Path, ...], ci_nanode: bool = False) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=GITEA_PUSH_YAML)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, nanode=ci_nanode) for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = GITEA_PUSH_YAML, nanode: bool = False) -> bool:
    modifications: set[Path] = set()
    with yield_job_with(
        "publish",
        "Build and publish the package",
        "dycw/action-publish-package@latest",
        path=path,
        modifications=modifications,
    ) as dict_:
        dict_["token-github"] = ACTION_TOKEN
        dict_["username"] = PYPI_GITEA_USERNAME
        dict_["password"] = PYPI_GITEA_READ_WRITE_TOKEN
        dict_["publish-url"] = PYPI_GITEA_PUBLISH_URL
    if nanode:
        _add_nanode(path=path, modifications=modifications)
    return len(modifications) == 0


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
        with_["token-github"] = ACTION_TOKEN
        with_["username"] = PYPI_NANODE_USERNAME
        with_["password"] = PYPI_NANODE_PASSWORD
        with_["publish-url"] = PYPI_NANODE_PUBLISH_URL
        with_["native-tls"] = True


if __name__ == "__main__":
    _main()
