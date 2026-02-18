from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.click import paths_argument
from pre_commit_hooks.constants import GITEA_PUSH_YAML
from pre_commit_hooks.hooks.setup_ci_push import _add_publish_package
from pre_commit_hooks.utilities import merge_paths, run_all_maybe_raise
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks._click import index_req_option
from qrt_pre_commit_hooks._constants import ACTION_TOKEN
from qrt_pre_commit_hooks._enums import Index
from qrt_pre_commit_hooks._settings import SETTINGS

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
@index_req_option
def cli(*, paths: tuple[Path, ...], index: Index) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=GITEA_PUSH_YAML)
    funcs: list[Callable[[], bool]] = [partial(_run, index, path=p) for p in paths_use]
    run_all_maybe_raise(*funcs)


def _run(index: Index, /, *, path: PathLike = GITEA_PUSH_YAML) -> bool:
    modifications: set[Path] = set()
    if index is Index.nanode:
        _add_publish_package(
            path=path,
            modifications=modifications,
            job_name_suffix="gitea",
            certificates=True,
            token_github=ACTION_TOKEN,
            username=SETTINGS.indexes.username(Index.gitea),
            password=SETTINGS.indexes.password(Index.gitea, write=True, ci=True),
            publish_url=SETTINGS.indexes.url(Index.gitea),
        )
    return len(modifications) == 0
