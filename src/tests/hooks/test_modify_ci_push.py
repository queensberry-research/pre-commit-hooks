from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITEA_PUSH_YAML
from utilities.core import normalize_multi_line_str

from qrt_pre_commit_hooks._enums import Index
from qrt_pre_commit_hooks.hooks._modify_ci_push import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestModifyCIPush:
    def test_nanode(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PUSH_YAML
        exp_output = normalize_multi_line_str("""
            jobs:
              publish-package-gitea:
                runs-on: ubuntu-latest
                steps:
                - name: Update CA certificates
                  run: sudo update-ca-certificates
                - name: Build and publish the package
                  uses: dycw/action-publish-package@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
                    username: qrt-bot
                    password: ${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}
                    publish_url: https://gitea.qrt:3000/api/packages/qrt/pypi
                    native-tls: true
        """)
        for i in range(2):
            result = _run(Index.nanode, path=path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output

    def test_gitea(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PUSH_YAML
        assert _run(Index.gitea, path=path)
        assert not path.exists()
