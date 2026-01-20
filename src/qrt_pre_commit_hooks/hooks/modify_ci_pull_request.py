from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import GITEA_PULL_REQUEST_YAML, paths_argument
from pre_commit_hooks.utilities import (
    get_partial_dict,
    get_set_dict,
    get_set_list_dicts,
    merge_paths,
    run_all_maybe_raise,
    yield_yaml_dict,
)
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks.constants import ACTION_TOKEN

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=GITEA_PULL_REQUEST_YAML)
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths_use]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = GITEA_PULL_REQUEST_YAML) -> bool:
    modifications: set[Path] = set()
    _add_github_token("pyright", path=path, modifications=modifications)
    _add_github_token("pytest", path=path, modifications=modifications)
    _add_github_token("ruff", path=path, modifications=modifications)
    return len(modifications) == 0


def _add_github_token(
    name: str,
    /,
    *,
    path: PathLike = GITEA_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        job = get_set_dict(jobs, name)
        steps = get_set_list_dicts(job, "steps")
        step = get_partial_dict(
            steps, {"name": f"Run '{name}'", "uses": f"dycw/action-{name}@latest"}
        )
        with_ = get_set_dict(step, "with")
        with_["token-github"] = ACTION_TOKEN


if __name__ == "__main__":
    _main()
