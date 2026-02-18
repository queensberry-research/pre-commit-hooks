from __future__ import annotations

from functools import partial
from pathlib import Path
from re import search
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.click import paths_argument
from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML, PYTHON_VERSION
from pre_commit_hooks.utilities import merge_paths, run_all_maybe_raise, yield_text_file
from utilities.click import CONTEXT_SETTINGS
from utilities.core import OneEmptyError, is_pytest, one, substitute

from qrt_pre_commit_hooks._constants import DOCKERFILE, ROOT_PEM
from qrt_pre_commit_hooks._settings import SETTINGS
from qrt_pre_commit_hooks._utilities import yield_add_hooks_args

if TYPE_CHECKING:
    from collections.abc import Callable

    from utilities.types import PathLike


@command(**CONTEXT_SETTINGS)
@paths_argument
def cli(*, paths: tuple[Path, ...]) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = []
    paths_use1 = merge_paths(*paths, target=DOCKERFILE, also_ok=ROOT_PEM)
    funcs.extend([partial(_run_dockerfile, path=p) for p in paths_use1])
    paths_use2 = merge_paths(*paths, target=ROOT_PEM, also_ok=DOCKERFILE)
    funcs.extend([partial(_run_root_pem, path=p) for p in paths_use2])
    run_all_maybe_raise(*funcs)


def _run_dockerfile(*, path: PathLike = DOCKERFILE) -> bool:
    modifications: set[Path] = set()
    with yield_add_hooks_args(
        path=Path(path).parent.parent / PRE_COMMIT_CONFIG_YAML
    ) as args:
        try:
            version = one(
                m.group(1)
                for a in args
                if (m := search(r"^--python-version=(\d+\.\d+)$", a)) is not None
            )
        except OneEmptyError:
            version = PYTHON_VERSION
    with yield_text_file(path, modifications=modifications) as context:
        text = substitute(
            SETTINGS.configs.dockerfile,
            mapping={"DOCKERFILE_DEFAULT_PYTHON_VERSION": version},
            safe=True,
        )
        context.output = text
    return len(modifications) == 0


def _run_root_pem(*, path: PathLike = ROOT_PEM) -> bool:
    modifications: set[Path] = set()
    with yield_text_file(path, modifications=modifications) as context:
        context.output = SETTINGS.configs.root_pem.read_text()
    return len(modifications) == 0
