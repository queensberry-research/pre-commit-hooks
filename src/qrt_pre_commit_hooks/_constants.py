from __future__ import annotations

ACTION_TOKEN = "${{secrets.ACTION_TOKEN}}"  # noqa: S105
GITEA_READ_TOKEN = "${{secrets.QRT_GITEA_READ_TOKEN}}"  # noqa: S105
GITEA_READ_WRITE_TOKEN = "${{secrets.QRT_GITEA_READ_WRITE_TOKEN}}"  # noqa: S105
NANODE_PYPI_PASSWORD = "${{secrets.NANODE_PYPI_PASSWORD}}"  # noqa: S105
SOPS_AGE_KEY = "${{secrets.SOPS_AGE_KEY}}"


__all__ = [
    "ACTION_TOKEN",
    "GITEA_READ_TOKEN",
    "GITEA_READ_WRITE_TOKEN",
    "NANODE_PYPI_PASSWORD",
    "SOPS_AGE_KEY",
]
