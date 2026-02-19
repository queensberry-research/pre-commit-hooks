from __future__ import annotations

import sys

from utilities.constants import MONTH
from utilities.core import is_debug, set_up_logging
from utilities.traceback import make_except_hook

from qrt_pre_commit_hooks._click import (
    index_req_option,
    package_option,
    package_req_option,
)
from qrt_pre_commit_hooks._constants import (
    ACTION_TOKEN,
    DOCKERFILE,
    GITEA_READ_TOKEN,
    GITEA_READ_WRITE_TOKEN,
    NANODE_PYPI_PASSWORD,
    QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL,
    ROOT_PEM,
    SOPS_AGE_KEY,
)
from qrt_pre_commit_hooks._enums import Index, Package
from qrt_pre_commit_hooks._settings import SETTINGS
from qrt_pre_commit_hooks._utilities import yield_add_hooks_args

__version__ = "0.5.23"


set_up_logging(__name__, files=".logs", log_version=__version__)
sys.excepthook = make_except_hook(
    path_max_age=MONTH, path=".logs/errors", version=__version__, pudb=is_debug
)


__all__ = [
    "ACTION_TOKEN",
    "DOCKERFILE",
    "GITEA_READ_TOKEN",
    "GITEA_READ_WRITE_TOKEN",
    "NANODE_PYPI_PASSWORD",
    "QUEENSBERRY_RESEARCH_PRE_COMMIT_HOOKS_URL",
    "ROOT_PEM",
    "SETTINGS",
    "SOPS_AGE_KEY",
    "Index",
    "Package",
    "index_req_option",
    "package_option",
    "package_req_option",
    "yield_add_hooks_args",
]
