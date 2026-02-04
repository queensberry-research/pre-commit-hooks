from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import PYPROJECT_TOML
from utilities.core import normalize_multi_line_str

from qrt_pre_commit_hooks._enums import Package
from qrt_pre_commit_hooks.hooks._modify_pyproject import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestModifyPyProject:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / PYPROJECT_TOML
        exp_output = normalize_multi_line_str(r"""
            [[tool.uv.index]]
            explicit = true
            name = "gitea"
            url = "https://qrt-bot:e43d1df41a3ecf96e4adbaf04e98cfaf094d253e@gitea.qrt:3000/api/packages/qrt/pypi/simple"

            [tool.uv.sources]
            backfill = {index = "gitea"}
            backtest = {index = "gitea"}
            database = {index = "gitea"}
            engine = {index = "gitea"}
            monitors = {index = "gitea"}
            optimizer = {index = "gitea"}
            qrt-click = {index = "gitea"}
            qrt-ib-async = {index = "gitea"}
            qrt-polars = {index = "gitea"}
            qrt-redis = {index = "gitea"}
            qrt-slack = {index = "gitea"}
            qrt-types = {index = "gitea"}
            qrt-utilities = {index = "gitea"}
            signals = {index = "gitea"}
            test-package = {index = "gitea"}
            testing = {index = "gitea"}
        """)
        for i in range(2):
            result = _run(Package.trading, path=path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
