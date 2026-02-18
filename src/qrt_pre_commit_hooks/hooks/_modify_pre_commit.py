from __future__ import annotations

from functools import partial
from pathlib import Path
from typing import TYPE_CHECKING

from click import command
from pre_commit_hooks.click import paths_argument
from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML, PRE_COMMIT_PRIORITY
from pre_commit_hooks.utilities import (
    ensure_contains,
    get_set_list_dicts,
    get_set_partial_dict,
    run_all_maybe_raise,
    yield_yaml_dict,
)
from utilities.click import CONTEXT_SETTINGS, flag
from utilities.core import is_pytest
from utilities.pydantic import extract_secret
from utilities.types import PathLike

from qrt_pre_commit_hooks._click import package_option
from qrt_pre_commit_hooks._constants import (
    ACTION_TOKEN,
    QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL,
    SOPS_AGE_KEY,
)
from qrt_pre_commit_hooks._settings import SETTINGS
from qrt_pre_commit_hooks._utilities import yield_add_hooks_args

if TYPE_CHECKING:
    from collections.abc import Callable, MutableSet
    from pathlib import Path

    from utilities.types import PathLike

    from qrt_pre_commit_hooks._enums import Index, Package


@command(**CONTEXT_SETTINGS)
@paths_argument
@flag("--ci-image", default=False)
@package_option
def cli(*, paths: tuple[Path, ...], ci_image: bool, package: Package | None) -> None:
    if is_pytest():
        return
    funcs: list[Callable[[], bool]] = [
        partial(_run, path=p, ci_image=ci_image, package=package) for p in paths
    ]
    run_all_maybe_raise(*funcs)


def _run(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    ci_image: bool = False,
    package: Package | None = None,
) -> bool:
    modifications: set[Path] = set()
    _add_ci_token_github(path=path, modifications=modifications)
    _add_pytest_sops_age_key(path=path, modifications=modifications)
    _add_priority(path=path, modifications=modifications)
    if ci_image:
        _add_ci_image(path=path, modifications=modifications)
    if package is not None:
        _add_index(package.pkg_index, path=path, modifications=modifications)
    return len(modifications) == 0


def _add_ci_image(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_add_hooks_args(path=path, modifications=modifications) as args:
        ensure_contains(
            args,
            f"--ci-image-registry-host={SETTINGS.gitea.host}",
            f"--ci-image-registry-port={SETTINGS.gitea.port}",
            f"--ci-image-registry-registry-username={SETTINGS.gitea.username}",
            f"--ci-image-registry-registry-password={SETTINGS.gitea.passwords.write}",
            f"--ci-image-namespace={SETTINGS.gitea.owner}",
        )


def _add_ci_token_github(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_add_hooks_args(path=path, modifications=modifications) as args:
        ensure_contains(args, f"--ci-token-github={ACTION_TOKEN}")


def _add_index(
    index: Index,
    /,
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_add_hooks_args(path=path, modifications=modifications) as args:
        settings = SETTINGS.indexes
        ensure_contains(
            args,
            f"--ci-python-index-password-read={extract_secret(settings.password(index, ci=True))}",
            f"--ci-python-index-password-write={extract_secret(settings.password(index, write=True, ci=True))}",
            f"--python-index-name={index.value}",
            f"--python-index-url={settings.url(index)}",
            f"--python-index-username={settings.username(index)}",
            f"--python-index-password={extract_secret(settings.password(index))}",
        )


def _add_priority(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_yaml_dict(path, modifications=modifications) as dict_:
        repos = get_set_list_dicts(dict_, "repos")
        repo = get_set_partial_dict(
            repos, {"repo": QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL}
        )
        hooks = get_set_list_dicts(repo, "hooks")
        hook = get_set_partial_dict(hooks, {"id": "add-qrt-hooks"})
        hook["priority"] = PRE_COMMIT_PRIORITY


def _add_pytest_sops_age_key(
    *,
    path: PathLike = PRE_COMMIT_CONFIG_YAML,
    modifications: MutableSet[Path] | None = None,
) -> None:
    with yield_add_hooks_args(path=path, modifications=modifications) as args:
        ensure_contains(args, f"--ci-pytest-sops-age-key={SOPS_AGE_KEY}")
