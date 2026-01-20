from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command, option
from pre_commit_hooks.constants import (
    PRE_COMMIT_CONFIG_YAML,
    paths_argument,
    python_option,
)
from pre_commit_hooks.hooks.add_hooks import _add_hook
from pre_commit_hooks.utilities import apply, run_all_maybe_raise
from utilities.click import CONTEXT_SETTINGS
from utilities.concurrent import concurrent_map
from utilities.os import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks.constants import QRT_PRE_COMMIT_HOOKS_URL

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import IntOrAll, PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@option("--ci", is_flag=True, default=False)
@python_option
def _main(
    *,
    paths: tuple[Path, ...],
    ci: bool = False,
    python: bool = False,
    max_workers: int | None = None,
) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [
        partial(
            _run,
            path=p,
            ci=ci,
            python=python,
            max_workers="all" if max_workers is None else max_workers,
        )
        for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    ci: bool = False,
    python: bool = False,
    max_workers: IntOrAll = "all",
) -> bool:
    funcs: list[Callable[[], bool]] = [partial(_add_modify_pre_commit, path=path)]
    if ci:
        funcs.append(partial(_add_modify_ci_pull_request, path=path))
        funcs.append(partial(_add_modify_ci_push, path=path))
    if python:
        funcs.append(partial(_add_modify_pyproject, path=path))
    return all(
        concurrent_map(apply, funcs, parallelism="threads", max_workers=max_workers)
    )


def _add_modify_ci_pull_request(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        QRT_PRE_COMMIT_HOOKS_URL,
        "modify-ci-pull-request",
        path=path,
        modifications=modifications,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_ci_push(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        QRT_PRE_COMMIT_HOOKS_URL,
        "modify-ci-push",
        path=path,
        modifications=modifications,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_pre_commit(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        QRT_PRE_COMMIT_HOOKS_URL,
        "modify-pre-commit",
        path=path,
        modifications=modifications,
        rev=True,
        type_="pre-commit",
    )
    return len(modifications) == 0


def _add_modify_pyproject(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        QRT_PRE_COMMIT_HOOKS_URL,
        "modify-pyproject",
        path=path,
        modifications=modifications,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
