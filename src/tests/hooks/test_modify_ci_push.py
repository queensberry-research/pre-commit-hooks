from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITEA_PUSH_YAML
from pre_commit_hooks.utilities import write_text
from utilities.core import normalize_multi_line_str

from qrt_pre_commit_hooks._enums import Package
from qrt_pre_commit_hooks.hooks._modify_ci_push import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestModifyCIPush:
    def test_none(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PUSH_YAML
        input_ = normalize_multi_line_str("""
            jobs:
              tag:
                steps:
                  - name: Tag the latest commit
                    uses: dycw/action-tag-commit@latest
        """)
        write_text(path, input_)
        exp_output = normalize_multi_line_str("""
            jobs:
              tag:
                steps:
                - name: Tag the latest commit
                  uses: dycw/action-tag-commit@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
          """)
        for i in range(2):
            result = _run(path=path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output

    def test_gitea(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PUSH_YAML
        input_ = normalize_multi_line_str("""
            jobs:
              publish:
                steps:
                  - name: Build and publish the package
                    uses: dycw/action-publish-package@latest
              tag:
                steps:
                  - name: Tag the latest commit
                    uses: dycw/action-tag-commit@latest
        """)
        write_text(path, input_)
        exp_output = normalize_multi_line_str("""
            jobs:
              publish:
                steps:
                - name: Build and publish the package
                  uses: dycw/action-publish-package@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
                    username: qrt-bot
                    password: ${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}
                    publish-url: https://gitea.qrt:3000/api/packages/qrt/pypi
              tag:
                steps:
                - name: Tag the latest commit
                  uses: dycw/action-tag-commit@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
        """)
        for i in range(2):
            result = _run(path=path, package=Package.trading)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output

    def test_infra(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PUSH_YAML
        input_ = normalize_multi_line_str("""
            jobs:
              tag:
                steps:
                  - name: Tag the latest commit
                    uses: dycw/action-tag-commit@latest
        """)
        write_text(path, input_)
        exp_output = normalize_multi_line_str("""
            jobs:
              tag:
                steps:
                - name: Tag the latest commit
                  uses: dycw/action-tag-commit@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
              publish:
                steps:
                - name: Build and publish the package
                  uses: dycw/action-publish-package@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
                    username: qrt-bot
                    password: ${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}
                    publish-url: https://gitea.qrt:3000/api/packages/qrt/pypi
              publish-nanode:
                runs-on: ubuntu-latest
                steps:
                - name: Update CA certificates
                  run: sudo update-ca-certificates
                - name: Build and publish the package
                  uses: dycw/action-publish-package@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
                    username: qrt
                    password: ${{secrets.PYPI_NANODE_PASSWORD}}
                    publish-url: https://pypi.queensberryresearch.com
                    native-tls: true
          """)
        for i in range(2):
            result = _run(path=path, package=Package.infra)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
