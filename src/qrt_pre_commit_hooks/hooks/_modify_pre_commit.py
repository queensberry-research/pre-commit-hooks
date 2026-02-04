from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import (
    PRE_COMMIT_CONFIG_YAML,
    PRE_COMMIT_PRIORITY,
    paths_argument,
)
from pre_commit_hooks.utilities import (
    get_set_list_dicts,
    get_set_partial_dict,
    run_all_maybe_raise,
    yield_yaml_dict,
)
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks._settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def cli(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = PRE_COMMIT_CONFIG_YAML) -> bool:
    modifications: set[Path] = set()
    _add_priority(path=path, modifications=modifications)
    return len(modifications) == 0


def _add_priority(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        repos = get_set_list_dicts(dict_, "repos")
        repo = get_set_partial_dict(repos, {"repo": SETTINGS.url})
        hooks = get_set_list_dicts(repo, "hooks")
        hook = get_set_partial_dict(hooks, {"id": "add-qrt-hooks"})
        hook["priority"] = PRE_COMMIT_PRIORITY


if __name__ == "__main__":
    cli()
