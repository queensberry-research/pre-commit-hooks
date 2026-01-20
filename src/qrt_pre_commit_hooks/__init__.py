from __future__ import annotations

import sys

from utilities.constants import MONTH
from utilities.logging import setup_logging
from utilities.os import is_debug
from utilities.traceback import make_except_hook

__version__ = "0.3.3"


setup_logging(logger=__name__, files_dir=".logs")
sys.excepthook = make_except_hook(
    path_max_age=MONTH, path=".logs/errors", version=__version__, pudb=is_debug
)


__all__ = []
