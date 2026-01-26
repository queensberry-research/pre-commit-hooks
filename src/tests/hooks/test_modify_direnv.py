from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import PRE_COMMIT_CONFIG_YAML
from utilities.core import normalize_multi_line_str

from qrt_pre_commit_hooks.hooks.modify_direnv import _get_text, _run

if TYPE_CHECKING:
    from pathlib import Path


class TestGetText:
    def test_main(self) -> None:
        result = _get_text("qrt")
        expected = normalize_multi_line_str("""
            # sops
            if [ -f "${HOME}/secrets/age/qrt.txt" ]; then
            \texport SOPS_AGE_KEY_FILE="${HOME}/secrets/age/qrt.txt"
            fi
        """)
        assert result == expected


class TestModifyDirenv:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / PRE_COMMIT_CONFIG_YAML
        for i in range(2):
            result = _run(path=path, name="key.txt")
            expected = i >= 1
            assert result is expected
            assert path.is_file()
