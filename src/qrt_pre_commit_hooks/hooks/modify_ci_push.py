from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.constants import GITEA_PUSH_YAML, paths_argument
from pre_commit_hooks.utilities import (
    get_partial_dict,
    get_set_dict,
    get_set_list_dicts,
    merge_paths,
    run_all_maybe_raise,
    yield_yaml_dict,
)
from utilities.click import CONTEXT_SETTINGS
from utilities.os import is_pytest
from utilities.types import PathLike

from qrt_pre_commit_hooks.constants import (
    ACTION_TOKEN,
    PYPI_GITEA_PUBLISH_URL,
    PYPI_GITEA_READ_WRITE_TOKEN,
    PYPI_GITEA_USERNAME,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def _main(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    paths_use = merge_paths(*paths, target=GITEA_PUSH_YAML)
    funcs: list[Callable[[], bool]] = [partial(_run, path=p) for p in paths_use]
    run_all_maybe_raise(*funcs)


def _run(*, path: PathLike = GITEA_PUSH_YAML) -> bool:
    modifications: set[Path] = set()
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        publish = get_set_dict(jobs, "publish")
        steps = get_set_list_dicts(publish, "steps")
        step = get_partial_dict(
            steps,
            {
                "name": "Build and publish the package",
                "uses": "dycw/action-publish-package@latest",
            },
        )
        with_ = get_set_dict(step, "with")
        with_["token-github"] = ACTION_TOKEN
        with_["username"] = PYPI_GITEA_USERNAME
        with_["password"] = PYPI_GITEA_READ_WRITE_TOKEN
        with_["publish-url"] = PYPI_GITEA_PUBLISH_URL
    return len(modifications) == 0


if __name__ == "__main__":
    _main()
