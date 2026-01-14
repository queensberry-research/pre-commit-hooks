from __future__ import annotations

from actions.utilities import LOADER
from typed_settings import load_settings, option, settings


@settings
class Settings:
    ci__pull_request__pre_commit: bool = option(
        default=False, help="Set up 'pull-request.yaml' pre-commit"
    )
    ci__pull_request__pre_commit__submodules: str | None = option(
        default=None, help="Set up CI 'pull-request.yaml' pre-commit with submodules"
    )
    ci__pull_request__pyright: bool = option(
        default=False, help="Set up 'pull-request.yaml' pyright"
    )
    ci__pull_request__pytest: bool = option(
        default=False, help="Set up 'pull-request.yaml' pytest"
    )
    ci__pull_request__pytest__all_versions: bool = option(
        default=False,
        help="Set up 'pull-request.yaml' pytest with the current version only",
    )
    ci__pull_request__pytest__sops_and_age: bool = option(
        default=False, help="Set up 'pull-request.yaml' pytest sops/age"
    )
    ci__pull_request__ruff: bool = option(
        default=False, help="Set up 'pull-request.yaml' ruff"
    )
    ci__push__pypi__gitea: bool = option(
        default=False, help="Set up 'push.yaml' with 'pypi-gitea'"
    )
    ci__push__pypi__nanode: bool = option(
        default=False, help="Set up 'push.yaml' with 'pypi-nanode'"
    )
    ci__push__tag: bool = option(default=False, help="Set up 'push.yaml' tagging")
    gitea_host: str = option(default="gitea.main", help="Gitea host")
    gitea_port: int = option(default=3000, help="Gitea port")
    pyproject: bool = option(default=False, help="Set up 'pyproject.toml'")
    pytest__timeout: int | None = option(
        default=None, help="Set up 'pytest.toml' timeout"
    )
    python_version: str = option(default="3.13", help="Python version")
    repo_name: str | None = option(default=None, help="Repo name")
    script: str | None = option(
        default=None, help="Set up a script instead of a package"
    )


SETTINGS = load_settings(Settings, [LOADER])


__all__ = ["SETTINGS", "Settings"]
