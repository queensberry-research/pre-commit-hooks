from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.click import paths_argument
from pre_commit_hooks.constants import PYPROJECT_TOML
from pre_commit_hooks.utilities import (
    get_set_table,
    merge_paths,
    run_all_maybe_raise,
    yield_tool_uv,
)
from tomlkit import inline_table
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks._click import package_req_option
from qrt_pre_commit_hooks._settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike

    from qrt_pre_commit_hooks._settings import Package


@command(**CONTEXT_SETTINGS)
@paths_argument
@package_req_option
def cli(*, paths: tuple[Path, ...], package: Package) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=PYPROJECT_TOML)
    funcs: list[Callable[[], bool]] = [
        partial(_run, package, path=p) for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(package: Package, /, *, path: PathLike = PYPROJECT_TOML) -> bool:
    modifications: set[Path] = set()
    _add_sources(package, path=path, modifications=modifications)
    return len(modifications) == 0


def _add_sources(
    package: Package,
    /,
    *,
    path: PathLike = PYPROJECT_TOML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    inner = inline_table()
    inner["index"] = package.pkg_index.value
    with yield_tool_uv(path, modifications=modifications) as uv:
        sources = get_set_table(uv, "sources")
        sources.clear()
        for package_i in sorted(SETTINGS.packages, key=lambda x: x.name):
            if package_i.type is package:
                sources[package_i.name] = inner
