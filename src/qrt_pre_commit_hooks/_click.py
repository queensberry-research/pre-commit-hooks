from __future__ import annotations

from utilities.click import Enum, option

from qrt_pre_commit_hooks._enums import Package

package_option = option(
    "--package", type=Enum(Package), default=None, help="The package type"
)
package_req_option = option(
    "--package", type=Enum(Package), required=True, help="The package type"
)


__all__ = ["package_option", "package_req_option"]
