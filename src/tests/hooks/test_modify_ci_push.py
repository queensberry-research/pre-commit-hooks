from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITEA_PUSH_YAML
from pre_commit_hooks.utilities import write_text
from utilities.text import strip_and_dedent

from qrt_pre_commit_hooks.hooks.modify_ci_push import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestModifyCIPush:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PUSH_YAML
        input_ = strip_and_dedent(
            """
            jobs:
              publish:
                steps:
                  - name: Build and publish the package
                    uses: dycw/action-publish-package@latest
            """,
            trailing=True,
        )
        write_text(path, input_)
        exp_output = strip_and_dedent(
            """
            jobs:
              publish:
                steps:
                - name: Build and publish the package
                  uses: dycw/action-publish-package@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
                    username: qrt-bot
                    password: ${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}
                    publish-url: https://gitea.main:3000/api/packages/qrt/pypi
              """,
            trailing=True,
        )
        for i in range(2):
            result = _run(path=path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
