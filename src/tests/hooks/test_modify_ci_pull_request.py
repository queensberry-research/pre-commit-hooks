from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITEA_PULL_REQUEST_YAML
from pre_commit_hooks.utilities import write_text
from utilities.core import normalize_multi_line_str

from qrt_pre_commit_hooks._enums import Index
from qrt_pre_commit_hooks.hooks._modify_ci_pull_request import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestModifyCIPullRequest:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PULL_REQUEST_YAML
        input_ = normalize_multi_line_str("""
            jobs:
              pyright:
                runs-on: ubuntu-latest
                steps:
                  - name: Run 'pyright'
                    uses: dycw/action-pyright@latest
              pytest:
                steps:
                  - name: Run 'pytest'
                    uses: dycw/action-pytest@latest
              ruff:
                runs-on: ubuntu-latest
                steps:
                  - name: Run 'ruff'
                    uses: dycw/action-ruff@latest
          """)
        write_text(path, input_)
        exp_output = normalize_multi_line_str("""
            jobs:
              pyright:
                runs-on: ubuntu-latest
                steps:
                - name: Run 'pyright'
                  uses: dycw/action-pyright@latest
                  with:
                    index: https://qrt-bot:${{secrets.PYPI_GITEA_READ_TOKEN}}@gitea.qrt:3000/api/packages/qrt/pypi/simple
                    token-github: ${{secrets.ACTION_TOKEN}}
              pytest:
                steps:
                - name: Run 'pytest'
                  uses: dycw/action-pytest@latest
                  with:
                    index: https://qrt-bot:${{secrets.PYPI_GITEA_READ_TOKEN}}@gitea.qrt:3000/api/packages/qrt/pypi/simple
                    sops-age-key: ${{secrets.SOPS_AGE_KEY}}
                    token-github: ${{secrets.ACTION_TOKEN}}
              ruff:
                runs-on: ubuntu-latest
                steps:
                - name: Run 'ruff'
                  uses: dycw/action-ruff@latest
                  with:
                    token-github: ${{secrets.ACTION_TOKEN}}
            """)
        for i in range(2):
            result = _run(Index.gitea, path=path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
