from __future__ import annotations

ACTION_TOKEN = "${{secrets.ACTION_TOKEN}}"  # noqa: S105
SOPS_AGE_KEY = "${{secrets.SOPS_AGE_KEY}}"
PYPI_GITEA_READ_TOKEN = "${{secrets.PYPI_GITEA_READ_TOKEN}}"  # noqa: S105
PYPI_GITEA_READ_WRITE_TOKEN = "${{secrets.PYPI_GITEA_READ_WRITE_TOKEN}}"  # noqa: S105
PYPI_NANODE_PASSWORD = "${{secrets.PYPI_NANODE_PASSWORD}}"  # noqa: S105


__all__ = [
    "ACTION_TOKEN",
    "PYPI_GITEA_READ_TOKEN",
    "PYPI_GITEA_READ_WRITE_TOKEN",
    "PYPI_NANODE_PASSWORD",
    "SOPS_AGE_KEY",
]
