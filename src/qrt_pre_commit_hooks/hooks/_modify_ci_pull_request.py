from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import GITEA_PULL_REQUEST_YAML, paths_argument
from pre_commit_hooks.utilities import merge_paths, run_all_maybe_raise
from utilities.click import CONTEXT_SETTINGS
from utilities.core import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks._click import package_req_option
from qrt_pre_commit_hooks._constants import ACTION_TOKEN, SOPS_AGE_KEY
from qrt_pre_commit_hooks._settings import SETTINGS
from qrt_pre_commit_hooks._utilities import yield_job_with

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator, MutableSet
    from pathlib import Path

    from utilities.types import PathLike, StrDict

    from qrt_pre_commit_hooks._enums import Index, Package


@command(**CONTEXT_SETTINGS)
@paths_argument
@package_req_option
def cli(*, paths: tuple[Path, ...], package: Package) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=GITEA_PULL_REQUEST_YAML)
    funcs: list[Callable[[], bool]] = [
        partial(_run, package.pkg_index, path=p) for p in paths_use
    ]
    run_all_maybe_raise(*funcs)


def _run(index: Index, /, *, path: PathLike = GITEA_PULL_REQUEST_YAML) -> bool:
    modifications: set[Path] = set()
    _add_index("pyright", index, path=path, modifications=modifications)
    _add_index("pytest", index, path=path, modifications=modifications)
    _add_sops_age_key(path=path, modifications=modifications)
    _add_token_github("pyright", path=path, modifications=modifications)
    _add_token_github("pytest", path=path, modifications=modifications)
    _add_token_github("ruff", path=path, modifications=modifications)
    return len(modifications) == 0


def _add_index(
    name: str,
    index: Index,
    /,
    *,
    path: PathLike = GITEA_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with _yield_pull_request_job_with(
        name, path=path, modifications=modifications
    ) as dict_:
        dict_["index"] = SETTINGS.indexes.get_read_url(index, visible=False)


def _add_token_github(
    name: str,
    /,
    *,
    path: PathLike = GITEA_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with _yield_pull_request_job_with(
        name, path=path, modifications=modifications
    ) as dict_:
        dict_["token-github"] = ACTION_TOKEN


def _add_sops_age_key(
    *,
    path: PathLike = GITEA_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with _yield_pull_request_job_with(
        "pytest", path=path, modifications=modifications
    ) as dict_:
        dict_["sops-age-key"] = SOPS_AGE_KEY


@contextmanager
def _yield_pull_request_job_with(
    name: str,
    /,
    *,
    path: PathLike = GITEA_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
) -> Iterator[StrDict]:
    with yield_job_with(
        name,
        f"Run '{name}'",
        f"dycw/action-{name}@latest",
        path=path,
        modifications=modifications,
    ) as dict_:
        yield dict_


if __name__ == "__main__":
    cli()
