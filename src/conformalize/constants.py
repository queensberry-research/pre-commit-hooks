from __future__ import annotations

API_PACKAGES_QRT_PYPI = "api/packages/qrt/pypi"
ACTION_TOKEN = "${{secrets.ACTION_TOKEN}}"  # noqa: S105
CONFORMALIZE_URL = "https://github.com/queensberry-research/conformalize"
PYPI_GITEA_USERNAME = "qrt-bot"
PYPI_GITEA_READ_TOKEN = "e43d1df41a3ecf96e4adbaf04e98cfaf094d253e"  # noqa: S105
PYPI_GITEA_READ_WRITE_TOKEN = "${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}"  # noqa: S105
PYPI_NANODE_USERNAME = "qrt"
PYPI_NANODE_PASSWORD = "${{secrets.PYPI_NANODE_PASSWORD}}"  # noqa: S105
SOPS_AGE_KEY = "${{secrets.SOPS_AGE_KEY}}"


__all__ = [
    "ACTION_TOKEN",
    "API_PACKAGES_QRT_PYPI",
    "CONFORMALIZE_URL",
    "PYPI_GITEA_READ_TOKEN",
    "PYPI_GITEA_READ_WRITE_TOKEN",
    "PYPI_GITEA_USERNAME",
    "PYPI_NANODE_PASSWORD",
    "PYPI_NANODE_USERNAME",
    "SOPS_AGE_KEY",
]
