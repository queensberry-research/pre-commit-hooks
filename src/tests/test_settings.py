from __future__ import annotations

from re import search

from pytest import mark, param
from utilities.pydantic import extract_secret

from qrt_pre_commit_hooks import SETTINGS
from qrt_pre_commit_hooks._enums import Index
from qrt_pre_commit_hooks._settings import _Settings


class TestSettings:
    def test_main(self) -> None:
        assert isinstance(SETTINGS, _Settings)

    @mark.parametrize("index", Index)
    def test_url(self, *, index: Index) -> None:
        result = SETTINGS.indexes.url(index)
        assert search(r"^https://", result) is not None

    @mark.parametrize("index", Index)
    def test_username(self, *, index: Index) -> None:
        result = SETTINGS.indexes.username(index)
        assert search(r"^qrt", result) is not None

    @mark.parametrize("index", Index)
    @mark.parametrize("write", [param(True), param(False)])
    def test_password_ci(self, *, index: Index, write: bool) -> None:
        result = extract_secret(SETTINGS.indexes.password(index, write=write, ci=True))
        assert search(r"^\${{secrets\.[A-Z_]+}}$", result) is not None
