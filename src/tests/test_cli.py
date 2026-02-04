from __future__ import annotations

from pre_commit_hooks.constants import ENVRC, PRE_COMMIT_CONFIG_YAML, PYPROJECT_TOML
from pytest import mark, param
from utilities.constants import HOUR
from utilities.pytest import throttle_test
from utilities.subprocess import run

from qrt_pre_commit_hooks._enums import Package


class TestCLI:
    @mark.parametrize(
        ("hook", "args"),
        [
            param(
                "add-qrt-hooks",
                [str(PRE_COMMIT_CONFIG_YAML), "--package", Package.trading.value],
            ),
            param(
                "modify-ci-pull-request",
                [str(PRE_COMMIT_CONFIG_YAML), "--package", Package.trading.value],
            ),
            param("modify-ci-push", [str(PRE_COMMIT_CONFIG_YAML)]),
            param(
                "modify-ci-push",
                [str(PRE_COMMIT_CONFIG_YAML), "--package", Package.trading.value],
            ),
            param("modify-direnv", [str(ENVRC)]),
            param("modify-direnv", [str(ENVRC), "--package", Package.trading.value]),
            param("modify-pre-commit", [str(PRE_COMMIT_CONFIG_YAML)]),
            param(
                "modify-pre-commit",
                [str(PRE_COMMIT_CONFIG_YAML), "--package", Package.trading.value],
            ),
            param(
                "modify-pyproject",
                [str(PYPROJECT_TOML), "--package", Package.trading.value],
            ),
        ],
    )
    @throttle_test(duration=HOUR)
    def test_main(self, *, hook: str, args: list[str]) -> None:
        run(hook, *args)
