from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML

from qrt_pre_commit_hooks.hooks.modify_direnv import _run

if TYPE_CHECKING:
    from pathlib import Path


class TestModifyDirenv:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / PRE_COMMIT_CONFIG_YAML
        for i in range(2):
            result = _run(path=path, sops="key.txt")
            expected = i >= 1
            assert result is expected
            assert path.is_file()
