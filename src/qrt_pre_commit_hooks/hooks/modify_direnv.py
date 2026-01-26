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

from qrt_pre_commit_hooks.constants import sops_option

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@sops_option
def _main(*, paths: tuple[Path, ...], sops: str | None = None) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=ENVRC)
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, name=sops) for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = ENVRC, name: str | None = None) -> bool:
    modifications: set[Path] = set()
    if name is not None:
        _add_sops(name, path=path, modifications=modifications)
    return len(modifications) == 0


def _add_sops(
    name: str,
    /,
    *,
    path: PathLike = ENVRC,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_text_file(path, modifications=modifications) as context:
        text = _get_text(name)
        if search(escape(text), context.output, flags=MULTILINE) is None:
            context.output += f"\n\n{text}"


def _get_text(name: str, /) -> str:
    path = f"${{HOME}}/secrets/age/{name}.txt"
    return normalize_multi_line_str(f"""
        # sops
        if [ -f "{path}" ]; then
        \texport SOPS_AGE_KEY_FILE="{path}"
        fi
    """)


if __name__ == "__main__":
    _main()
