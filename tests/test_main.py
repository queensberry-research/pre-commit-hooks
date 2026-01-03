from __future__ import annotations

from utilities.pathlib import get_repo_root
from utilities.subprocess import run


class TestScript:
    def test_main(self) -> None:
        run("./script.py", cwd=get_repo_root())
