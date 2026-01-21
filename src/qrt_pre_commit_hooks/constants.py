from __future__ import annotations

from click import option

API_PACKAGES_QRT_PYPI = "api/packages/qrt/pypi"


ACTION_TOKEN = "${{secrets.ACTION_TOKEN}}"  # noqa: S105
SOPS_AGE_KEY = "${{secrets.SOPS_AGE_KEY}}"


GITEA_HOST = "gitea.main"
GITEA_PORT = 3000


PACKAGES = {
    "backfill",
    "backtest",
    "database",
    "engine",
    "infra-utilities",
    "monitors",
    "mount",
    "nanode",
    "optimizer",
    "proxmox",
    "qrt-click",
    "qrt-ib-async",
    "qrt-polars",
    "qrt-redis",
    "qrt-slack",
    "qrt-types",
    "qrt-utilities",
    "signals",
    "test-package",
    "testing",
}


PYPI_GITEA_USERNAME = "qrt-bot"
PYPI_GITEA_READ_TOKEN = "e43d1df41a3ecf96e4adbaf04e98cfaf094d253e"  # noqa: S105
PYPI_GITEA_READ_WRITE_TOKEN = "${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}"  # noqa: S105
PYPI_GITEA_READ_URL = f"https://{PYPI_GITEA_USERNAME}:{PYPI_GITEA_READ_TOKEN}@{GITEA_HOST}:{GITEA_PORT}/{API_PACKAGES_QRT_PYPI}/simple"
PYPI_GITEA_PUBLISH_URL = f"https://{GITEA_HOST}:{GITEA_PORT}/{API_PACKAGES_QRT_PYPI}"


PYPI_NANODE_USERNAME = "qrt"
PYPI_NANODE_PASSWORD = "${{secrets.PYPI_NANODE_PASSWORD}}"  # noqa: S105
PYPI_NANODE_PUBLISH_URL = "https://pypi.queensberryresearch.com"


QRT_PRE_COMMIT_HOOKS_URL = "https://github.com/queensberry-research/pre-commit-hooks"


ci_nanode_option = option("--ci-nanode", is_flag=True, default=False)
sops_option = option("--sops", type=str, default=None)


__all__ = [
    "ACTION_TOKEN",
    "API_PACKAGES_QRT_PYPI",
    "GITEA_HOST",
    "GITEA_PORT",
    "PACKAGES",
    "PYPI_GITEA_PUBLISH_URL",
    "PYPI_GITEA_READ_TOKEN",
    "PYPI_GITEA_READ_URL",
    "PYPI_GITEA_READ_WRITE_TOKEN",
    "PYPI_GITEA_USERNAME",
    "PYPI_NANODE_PASSWORD",
    "PYPI_NANODE_PUBLISH_URL",
    "PYPI_NANODE_USERNAME",
    "QRT_PRE_COMMIT_HOOKS_URL",
    "SOPS_AGE_KEY",
    "ci_nanode_option",
    "sops_option",
]
