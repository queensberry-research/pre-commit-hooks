from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML, paths_argument
from pre_commit_hooks.hooks.add_hooks import _add_hook
from pre_commit_hooks.utilities import run_all, run_all_maybe_raise
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks._click import package_option
from qrt_pre_commit_hooks._settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike

    from qrt_pre_commit_hooks._enums import Package


@command(**CONTEXT_SETTINGS)
@paths_argument
@package_option
def cli(*, paths: tuple[Path, ...], package: Package | None) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, package=package) for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PRE_COMMIT_CONFIG_YAML, package: Package | None) -> bool:
    funcs: list[Callable[[], bool]] = [
        partial(_add_modify_ci_push, path=path, package=package),
        partial(_add_modify_direnv, path=path, package=package),
        partial(_add_modify_pre_commit, path=path, package=package),
    ]
    if package is not None:
        funcs.append(partial(_add_modify_ci_pull_request, package, path=path))
        funcs.append(partial(_add_modify_pyproject, package, path=path))
    return run_all(*funcs)


def _add_modify_ci_pull_request(
    package: Package, /, *, path: PathLike = PRE_COMMIT_CONFIG_YAML
) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        SETTINGS.url,
        "modify-ci-pull-request",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=[f"--package={package.value}"],
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_ci_push(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, package: Package | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if package is not None:
        args.append(f"--package={package.value}")
    _add_hook(
        SETTINGS.url,
        "modify-ci-push",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_direnv(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, package: Package | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if package is not None:
        args.append(f"--package={package.value}")
    _add_hook(
        SETTINGS.url,
        "modify-direnv",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_pre_commit(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, package: Package | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = []
    if package is not None:
        args.append(f"--package={package.value}")
    _add_hook(
        SETTINGS.url,
        "modify-pre-commit",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=args if len(args) >= 1 else None,
        type_="pre-commit",
    )
    return len(modifications) == 0


def _add_modify_pyproject(
    package: Package, /, *, path: PathLike = PRE_COMMIT_CONFIG_YAML
) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        SETTINGS.url,
        "modify-pyproject",
        path=path,
        modifications=modifications,
        rev=True,
        args_exact=[f"--package={package.value}"],
        type_="editor",
    )
    return len(modifications) == 0


if __name__ == "__main__":
    cli()
