from __future__ import annotations

import sys

from utilities.constants import MONTH
from utilities.core import is_debug, set_up_logging
from utilities.traceback import make_except_hook

__version__ = "0.3.28"


set_up_logging(__name__, files=".logs")
sys.excepthook = make_except_hook(
    path_max_age=MONTH, path=".logs/errors", version=__version__, pudb=is_debug
)


__all__ = []
