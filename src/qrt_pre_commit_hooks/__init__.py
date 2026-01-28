from __future__ import annotations

import sys

from utilities.constants import MONTH
from utilities.core import is_debug
from utilities.logging import setup_logging
from utilities.traceback import make_except_hook

__version__ = "0.3.23"


setup_logging(__name__, files_dir=".logs")
sys.excepthook = make_except_hook(
    path_max_age=MONTH, path=".logs/errors", version=__version__, pudb=is_debug
)


__all__ = []
