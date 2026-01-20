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
from pre_commit_hooks.utilities import run_all, run_all_maybe_raise
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks.constants import (
    QRT_PRE_COMMIT_HOOKS_URL,
    ci_nanode_option,
    sops_option,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@option("--ci", is_flag=True, default=False)
@ci_nanode_option
@python_option
@sops_option
def _main(
    *,
    paths: tuple[Path, ...],
    ci: bool = False,
    ci_nanode: bool = False,
    python: bool = False,
    sops: str | None = None,
) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, ci=ci, ci_nanode=ci_nanode, python=python, sops=sops)
        for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    ci: bool = False,
    ci_nanode: bool = False,
    python: bool = False,
    sops: str | None = None,
) -> bool:
    funcs: list[Callable[[], bool]] = [partial(_add_modify_pre_commit, path=path)]
    if ci:
        funcs.append(partial(_add_modify_ci_pull_request, path=path, sops=sops))
        funcs.append(partial(_add_modify_ci_push, path=path, ci_nanode=ci_nanode))
    if python:
        funcs.append(partial(_add_modify_pyproject, path=path))
    if sops:
        funcs.append(partial(_add_modify_direnv, path=path, sops=sops))
    return run_all(*funcs)


def _add_modify_ci_pull_request(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, sops: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if sops is not None:
        args.append(f"--sops={sops}")
    _add_hook(
        QRT_PRE_COMMIT_HOOKS_URL,
        "modify-ci-pull-request",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_ci_push(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, ci_nanode: bool = False
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if ci_nanode:
        args.append("--ci-nanode")
    _add_hook(
        QRT_PRE_COMMIT_HOOKS_URL,
        "modify-ci-push",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_direnv(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, sops: str | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if sops is not None:
        args.append(f"--sops={sops}")
    _add_hook(
        QRT_PRE_COMMIT_HOOKS_URL,
        "modify-direnv",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
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
