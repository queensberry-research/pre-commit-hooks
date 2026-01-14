from __future__ import annotations

from click import command
from typed_settings import click_options
from utilities.click import CONTEXT_SETTINGS
from utilities.logging import basic_config
from utilities.os import is_pytest

from conformalize.lib import conformalize
from conformalize.logging import LOGGER
from conformalize.settings import LOADER, Settings


@command(**CONTEXT_SETTINGS)
@click_options(Settings, [LOADER], show_envvars_in_help=True)
def _main(settings: Settings, /) -> None:
    if is_pytest():
        return
    basic_config(obj=LOGGER)
    conformalize(
        ci__pull_request__pre_commit=settings.ci__pull_request__pre_commit,
        ci__pull_request__pre_commit__submodules=settings.ci__pull_request__pre_commit__submodules,
        ci__pull_request__pyright=settings.ci__pull_request__pyright,
        ci__pull_request__pytest=settings.ci__pull_request__pytest,
        ci__pull_request__pytest__all_versions=settings.ci__pull_request__pytest__all_versions,
        ci__pull_request__pytest__sops_and_age=settings.ci__pull_request__pytest__sops_and_age,
        ci__pull_request__ruff=settings.ci__pull_request__ruff,
        ci__push__pypi__gitea=settings.ci__push__pypi__gitea,
        ci__push__pypi__nanode=settings.ci__push__pypi__nanode,
        ci__push__tag=settings.ci__push__tag,
        gitea_host=settings.gitea_host,
        gitea_port=settings.gitea_port,
        pyproject=settings.pyproject,
        pytest__timeout=settings.pytest__timeout,
        python_version=settings.python_version,
        repo_name=settings.repo_name,
        script=settings.script,
    )


if __name__ == "__main__":
    _main()
