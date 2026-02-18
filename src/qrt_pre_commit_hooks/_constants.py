from __future__ import annotations

from pathlib import Path

ACTION_TOKEN = "${{secrets.ACTION_TOKEN}}"  # noqa: S105
GITEA_READ_TOKEN = "${{secrets.QRT_GITEA_READ_TOKEN}}"  # noqa: S105
GITEA_READ_WRITE_TOKEN = "${{secrets.QRT_GITEA_READ_WRITE_TOKEN}}"  # noqa: S105
NANODE_PYPI_PASSWORD = "${{secrets.NANODE_PYPI_PASSWORD}}"  # noqa: S105
SOPS_AGE_KEY = "${{secrets.SOPS_AGE_KEY}}"


DOCKERFILE = Path("docker/Dockerfile")
ROOT_PEM = Path("docker/root.pem")


QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL = (
    "https://github.com/queensberry-research/pre-commit-hooks"
)


__all__ = [
    "ACTION_TOKEN",
    "DOCKERFILE",
    "GITEA_READ_TOKEN",
    "GITEA_READ_WRITE_TOKEN",
    "NANODE_PYPI_PASSWORD",
    "QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL",
    "ROOT_PEM",
    "SOPS_AGE_KEY",
]
