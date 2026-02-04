from __future__ import annotations

from re import search

from pytest import mark, param

from qrt_pre_commit_hooks import SETTINGS
from qrt_pre_commit_hooks._settings import _Settings


class TestSettings:
    def test_main(self) -> None:
        assert isinstance(SETTINGS, _Settings)

    @mark.parametrize(
        ("visible", "expected"),
        [
            param(None, "https://gitea.qrt:3000/api/packages/qrt/pypi/simple"),
            param(
                False,
                "https://qrt-bot:${{secrets.PYPI_GITEA_READ_TOKEN}}@gitea.qrt:3000/api/packages/qrt/pypi/simple",
            ),
        ],
    )
    def test_read_url(self, *, visible: bool | None, expected: str) -> None:
        result = SETTINGS.indexes.gitea.read_url(visible=visible)
        assert result == expected

    def test_read_url_visible(self) -> None:
        result = SETTINGS.indexes.gitea.read_url(visible=True)
        pattern = r"https://qrt-bot:\w+@gitea\.qrt:3000/api/packages/qrt/pypi/simple"
        assert search(pattern, result) is not None
