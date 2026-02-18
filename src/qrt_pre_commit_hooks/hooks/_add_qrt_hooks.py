from __future__ import annotations

from collections.abc import Callable
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.click import paths_argument
from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML, PYPROJECT_TOML
from pre_commit_hooks.hooks.add_hooks import _add_hook
from pre_commit_hooks.utilities import (
    get_table,
    merge_paths,
    run_all,
    run_all_maybe_raise,
    yield_toml_doc,
)
from utilities.click import CONTEXT_SETTINGS, to_args
from utilities.core import OneEmptyError, is_pytest, one
from utilities.types import PathLike

from qrt_pre_commit_hooks._constants import QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL
from qrt_pre_commit_hooks._settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Callable

    from utilities.types import PathLike

    from qrt_pre_commit_hooks._enums import Index, Package


@command(**CONTEXT_SETTINGS)
@paths_argument
def cli(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    package = _get_package(path=path)
    funcs: list[Callable[[], bool]] = [
        partial(_add_modify_direnv, path=path, package=package),
        partial(_add_modify_pre_commit, path=path, package=package),
    ]
    if _has_scripts(path=Path(path).parent / PYPROJECT_TOML):
        funcs.append(partial(_add_setup_docker, path=path))
    if package is not None:
        funcs.append(partial(_add_modify_ci_push, package.pkg_index, path=path))
        funcs.append(partial(_add_modify_pyproject, package, path=path))
    return run_all(*funcs)


def _add_modify_ci_push(
    index: Index, /, *, path: PathLike = PRE_COMMIT_CONFIG_YAML
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args("--index", index, join=True)
    _add_hook(
        QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL,
        "modify-ci-push",
        path=path,
        modifications=modifications,
        rev=True,
        args=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_direnv(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, package: Package | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args("--package", package, join=True)
    _add_hook(
        QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL,
        "modify-direnv",
        path=path,
        modifications=modifications,
        rev=True,
        args=args if len(args) >= 1 else None,
        type_="editor",
    )
    return len(modifications) == 0


def _add_modify_pre_commit(
    *, path: PathLike = PRE_COMMIT_CONFIG_YAML, package: Package | None = None
) -> bool:
    modifications: set[Path] = set()
    args: list[str] = to_args("--package", package, join=True)
    _add_hook(
        QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL,
        "modify-pre-commit",
        path=path,
        modifications=modifications,
        rev=True,
        args=args if len(args) >= 1 else None,
        type_="pre-commit",
    )
    return len(modifications) == 0


def _add_modify_pyproject(
    package: Package, /, *, path: PathLike = PRE_COMMIT_CONFIG_YAML
) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL,
        "modify-pyproject",
        path=path,
        modifications=modifications,
        rev=True,
        args=[f"--package={package.value}"],
        type_="editor",
    )
    return len(modifications) == 0


def _add_setup_docker(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_hook(
        QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL,
        "setup-docker",
        path=path,
        modifications=modifications,
        rev=True,
        type_="editor",
    )
    return len(modifications) == 0


def _get_package(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> Package | None:
    path_use = one(merge_paths(path, target=PYPROJECT_TOML))
    with yield_toml_doc(path_use) as doc:
        project = get_table(doc, "project")
    name = project["name"]
    try:
        return one(p.type for p in SETTINGS.packages if p.name == name)
    except OneEmptyError:
        return None


def _has_scripts(*, path: PathLike = PYPROJECT_TOML) -> bool:
    with yield_toml_doc(path) as doc:
        project = get_table(doc, "project")
        try:
            _ = get_table(project, "scripts")
        except KeyError:
            return False
        return True
