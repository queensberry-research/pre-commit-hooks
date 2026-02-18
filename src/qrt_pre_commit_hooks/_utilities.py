from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from pre_commit_hooks.constants import DYCW_PRE_COMMIT_HOOKS_URL, PRE_COMMIT_CONFIG_YAML
from pre_commit_hooks.utilities import (
    get_set_list_dicts,
    get_set_list_strs,
    get_set_partial_dict,
    yield_yaml_dict,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSet
    from pathlib import Path

    from utilities.types import PathLike


@contextmanager
def yield_add_hooks_args(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
) -> Iterator[list[str]]:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        repos = get_set_list_dicts(dict_, "repos")
        repo = get_set_partial_dict(repos, {"repo": DYCW_PRE_COMMIT_HOOKS_URL})
        hooks = get_set_list_dicts(repo, "hooks")
        hook = get_set_partial_dict(hooks, {"id": "add-hooks"})
        yield get_set_list_strs(hook, "args")


__all__ = ["yield_add_hooks_args"]
