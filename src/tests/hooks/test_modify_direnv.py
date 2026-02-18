from __future__ import annotations

from typing import TYPE_CHECKING

from pre_commit_hooks.constants import ENVRC
from utilities.core import check_multi_line_regex, normalize_multi_line_str

from qrt_pre_commit_hooks._enums import Package
from qrt_pre_commit_hooks.hooks._modify_direnv import _get_sops_text, _run

if TYPE_CHECKING:
    from pathlib import Path


class TestGetText:
    def test_sops(self) -> None:
        result = _get_sops_text(Package.trading)
        expected = normalize_multi_line_str("""
            # sops
            if [ -f "${HOME}/secrets/age/trading.txt" ]; then
            \texport SOPS_AGE_KEY_FILE="${HOME}/secrets/age/trading.txt"
            fi
        """)
        assert result == expected


class TestModifyDirenv:
    def test_main(self, *, tmp_path: Path) -> None:
        path = tmp_path / ENVRC
        exp_output = normalize_multi_line_str(r"""
            # sops
            if \[ -f "\${HOME}/secrets/age/trading.txt" \]; then
            \texport SOPS_AGE_KEY_FILE="\${HOME}/secrets/age/trading.txt"
            fi
        """)
        for i in range(2):
            result = _run(path=path, package=Package.trading)
            exp_result = i >= 1
            assert result is exp_result
            contents = path.read_text()
            check_multi_line_regex(exp_output, contents)
