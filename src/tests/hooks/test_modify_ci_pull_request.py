from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import GITEA_PULL_REQUEST_YAML
from pre_commit_hooks.utilities import write_text
from utilities.text import strip_and_dedent

from qrt_pre_commit_hooks.constants import PYPI_GITEA_READ_URL
from qrt_pre_commit_hooks.hooks.modify_ci_pull_request import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestModifyCIPullRequest:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / GITEA_PULL_REQUEST_YAML
        input_ = strip_and_dedent(
            """
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
            """,
            trailing=True,
        )
        write_text(path, input_)
        exp_output = strip_and_dedent(
            f"""
            jobs:
              pyright:
                runs-on: ubuntu-latest
                steps:
                - name: Run 'pyright'
                  uses: dycw/action-pyright@latest
                  with:
                    index: {PYPI_GITEA_READ_URL}
                    token-github: ${{{{secrets.ACTION_TOKEN}}}}
              pytest:
                steps:
                - name: Run 'pytest'
                  uses: dycw/action-pytest@latest
                  with:
                    index: {PYPI_GITEA_READ_URL}
                    token-github: ${{{{secrets.ACTION_TOKEN}}}}
              ruff:
                runs-on: ubuntu-latest
                steps:
                - name: Run 'ruff'
                  uses: dycw/action-ruff@latest
                  with:
                    token-github: ${{{{secrets.ACTION_TOKEN}}}}
              """,
            trailing=True,
        )
        for i in range(2):
            result = _run(path=path)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            assert contents == exp_output
