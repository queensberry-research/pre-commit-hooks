from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITEA_PULL_REQUEST_YAML
from pre_commit_hooks.utilities import (
    get_partial_dict,
    get_set_dict,
    get_set_list_dicts,
    yield_yaml_dict,
)

if TYPE_CHECKING:
    from collections.abc import Iterator, MutableSet
    from pathlib import Path

    from utilities.types import PathLike, StrDict


@contextmanager
def yield_job_with(
    job_name: str,
    step_name: str,
    step_uses: str,
    /,
    *,
    path: PathLike = GITEA_PULL_REQUEST_YAML,
    modifications: MutableSet[Path] | None = None,
) -> Iterator[StrDict]:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        jobs = get_set_dict(dict_, "jobs")
        job = get_set_dict(jobs, job_name)
        steps = get_set_list_dicts(job, "steps")
        step = get_partial_dict(steps, {"name": step_name, "uses": step_uses})
        yield get_set_dict(step, "with")


__all__ = ["yield_job_with"]
