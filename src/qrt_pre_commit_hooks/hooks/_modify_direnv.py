from __future__ import annotations

from functools import partial
from pathlib import Path
from re import MULTILINE, escape, search
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import ENVRC, paths_argument
from pre_commit_hooks.utilities import merge_paths, run_all_maybe_raise, yield_text_file
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest, normalize_multi_line_str
from utilities.types import PathLike

from qrt_pre_commit_hooks._click import package_option
from qrt_pre_commit_hooks._settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike

    from qrt_pre_commit_hooks._enums import Index, Package


@command(**CONTEXT_SETTINGS)
@paths_argument
@package_option
def cli(*, paths: tuple[Path, ...], package: Package | None) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=ENVRC)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, package=package) for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = ENVRC, package: Package | None = None) -> bool:
    modifications: set[Path] = set()
    if package is not None:
        _add_sops(package, path=path, modifications=modifications)
        _add_uv(package.pkg_index, path=path, modifications=modifications)
    return len(modifications) == 0


def _add_sops(
    package: Package,
    /,
    *,
    path: PathLike = ENVRC,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_text_file(path, modifications=modifications) as context:
        text = _get_sops_text(package)
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"


def _get_sops_text(package: Package, /) -> str:
    path = f"${{HOME}}/secrets/age/{package.value}.txt"
    return normalize_multi_line_str(f"""
        # sops
        if [ -f "{path}" ]; then
        \texport SOPS_AGE_KEY_FILE="{path}"
        fi
    """)


def _add_uv(
    index: Index,
    /,
    *,
    path: PathLike = ENVRC,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_text_file(path, modifications=modifications) as context:
        text = _get_uv_text(index)
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"


def _get_uv_text(index: Index, /) -> str:
    name = index.value.upper()
    username = SETTINGS.indexes.get_username(index)
    password = SETTINGS.indexes.get_read_password(index, visible=True)
    return normalize_multi_line_str(f"""
        # uv index
        export UV_INDEX_{name}_USERNAME='{username}'
        export UV_INDEX_{name}_PASSWORD='{password}'
    """)


if __name__ == "__main__":
    cli()
