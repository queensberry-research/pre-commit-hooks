from __future__ import annotations

ACTION_TOKEN = "${{secrets.ACTION_TOKEN}}"  # noqa: S105
SOPS_AGE_KEY = "${{secrets.SOPS_AGE_KEY}}"


__all__ = ["ACTION_TOKEN", "SOPS_AGE_KEY"]
