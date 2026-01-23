from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import PYPROJECT_TOML, paths_argument
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_table,
    merge_paths,
    run_all_maybe_raise,
    yield_tool_uv,
    yield_tool_uv_index,
)
from tomlkit import inline_table, table
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks.constants import PACKAGES, PYPI_GITEA_READ_URL

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYPROJECT_TOML)
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths_use]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    _add_gitea_index(path=path, modifications=modifications)
    _add_gitea_sources(path=path, modifications=modifications)
    return len(modifications) == 0


def _add_gitea_index(
    *, path: PathLike = PYPROJECT_TOML, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_tool_uv_index(path, modifications=modifications) as index:
        tab = table()
        tab["explicit"] = True
        tab["name"] = "gitea"
        tab["url"] = PYPI_GITEA_READ_URL
        ensure_contains(index, tab)


def _add_gitea_sources(
    *, path: PathLike = PYPROJECT_TOML, modifications: MutableSet[Path] | None = None
) -> None:
    with yield_tool_uv(path, modifications=modifications) as uv:
        sources = get_set_table(uv, "sources")
        sources.clear()
        inner = inline_table()
        inner["index"] = "gitea"
        for package in sorted(PACKAGES):
            sources[package] = inner


if __name__ == "__main__":
    _main()
