#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.12"
# dependencies = [
#   "click >=8.3.1, <8.4",
#   "dycw-utilities >=0.175.36, <0.176",
#   "rich >=14.2.0, <14.3",
#   "ruamel-yaml >=0.19.0, <0.20",
#   "tomlkit >=0.13.3, <0.14",
#   "typed-settings[attrs, click] >=25.3.0, <25.4",
#   "pyright",
#   "pytest-xdist",
# ]
# ///
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
from logging import getLogger
from pathlib import Path
from typing import TYPE_CHECKING, Any

import yaml
from click import command
from rich.pretty import pretty_repr
from tomlkit.container import Container
from tomlkit.items import AoT, Array, Table
from typed_settings import click_options, option, settings
from utilities.atomicwrites import writer
from utilities.click import CONTEXT_SETTINGS
from utilities.functions import ensure_class
from utilities.logging import basic_config

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator

    from tomlkit.container import Container
    from utilities.types import PathLike


type HasAppend = Array | list[Any]
type HasSetDefault = Container | StrDict | Table
type StrDict = dict[str, Any]
_LOGGER = getLogger(__name__)
_MODIFIED = ContextVar("modified", default=False)


@settings
class Settings:
    gitea__push__tag: bool = option(default=False, help="Set up 'push.yaml' with 'tag'")
    gitea__push__pypi: bool = option(
        default=False, help="Set up 'push.yaml' with 'pypi'"
    )
    gitea__push__docker: bool = option(
        default=False, help="Set up 'push.yaml' with 'docker'"
    )
    dry_run: bool = option(default=False, help="Dry run the CLI")


_SETTINGS = Settings()


@command(**CONTEXT_SETTINGS)
@click_options(Settings, "app", show_envvars_in_help=True)
def main(settings: Settings, /) -> None:
    _LOGGER.info("Running with settings:\n%s", pretty_repr(settings))
    if settings.dry_run:
        _LOGGER.info("Dry run; exiting...")
        return
    if (
        settings.gitea__push__tag
        or settings.gitea__push__pypi
        or settings.gitea__push__docker
    ):
        _add_github_push_yaml(
            tag=settings.gitea__push__tag,
            pypi=settings.gitea__push__pypi,
            docker=settings.gitea__push__docker,
        )


def _add_github_push_yaml(
    *,
    tag: bool = _SETTINGS.gitea__push__tag,
    pypi: bool = _SETTINGS.gitea__push__pypi,
    docker: bool = _SETTINGS.gitea__push__docker,
) -> None:
    with _yield_yaml_dict(".gitea/workflows/push.yaml") as dict_:
        dict_["name"] = "push"
        on = _get_dict(dict_, "on")
        push = _get_dict(on, "push")
        branches = _get_list(push, "branches")
        _ensure_contains(branches, "master")
        jobs = _get_dict(dict_, "jobs")
        if tag:
            tag_dict = _get_dict(jobs, "tag")
            tag_dict["runs-on"] = "ubuntu-latest"
            steps = _get_list(tag_dict, "steps")
            steps[:] = [
                {
                    "name": "Update CA certificates",
                    "run": "sudo update-ca-certificates",
                },
                {"name": "Tag latest commit", "uses": "dycw/action-tag-commit@latest"},
            ]
        if pypi:
            pypi_dict = _get_dict(jobs, "pypi")
            pypi_dict["runs-on"] = "ubuntu-latest"
            steps = _get_list(pypi_dict, "steps")
            steps[:] = [
                {
                    "name": "Update CA certificates",
                    "run": "sudo update-ca-certificates",
                },
                {
                    "name": "Build Python package and upload distribution",
                    "uses": "dycw/action-uv-publish@latest",
                    "with": {
                        "username": "qrt-bot",
                        "password": "${{ secrets.ACTION_UV_PUBLISH_PASSWORD }}",
                        "publish-url": "https://gitlab.main:3000/api/packages/qrt/pypi/",
                        "native-tls": True,
                    },
                },
            ]
        if docker:
            raise NotImplementedError


def _ensure_aot_contains(array: AoT, /, *tables: Table) -> None:
    for table_ in tables:
        if table_ not in array:
            array.append(table_)


def _ensure_contains(array: HasAppend, /, *objs: Any) -> None:
    if isinstance(array, AoT):
        msg = f"Use {_ensure_aot_contains.__name__!r} instead of {_ensure_contains.__name__!r}"
        raise TypeError(msg)
    for obj in objs:
        if obj not in array:
            array.append(obj)


def _get_dict(container: HasSetDefault, key: str, /) -> StrDict:
    return ensure_class(container.setdefault(key, {}), dict)


def _get_list(container: HasSetDefault, key: str, /) -> list[Any]:
    return ensure_class(container.setdefault(key, []), list)


@contextmanager
def _yield_write_context[T](
    path: PathLike,
    loads: Callable[[str], T],
    get_default: Callable[[], T],
    dumps: Callable[[T], str],
    /,
) -> Iterator[T]:
    path = Path(path)

    def run(verb: str, data: T, /) -> None:
        _LOGGER.info("%s '%s'...", verb, path)
        with writer(path, overwrite=True) as temp:
            _ = temp.write_text(dumps(data))
        _ = _MODIFIED.set(True)

    try:
        data = loads(path.read_text())
    except FileNotFoundError:
        yield (default := get_default())
        run("Writing", default)
    else:
        yield data
        current = loads(path.read_text())
        if data != current:
            run("Modifying", data)


@contextmanager
def _yield_yaml_dict(path: PathLike, /) -> Iterator[StrDict]:
    with _yield_write_context(path, yaml.safe_load, dict, yaml.safe_dump) as dict_:
        yield dict_


if __name__ == "__main__":
    basic_config(obj=__name__)
    main()
