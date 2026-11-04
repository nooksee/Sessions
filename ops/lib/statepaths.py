"""No-write checks for explicitly reviewed runtime-state path migrations.

This library is not a migrator. It never adopts, copies or removes state.
Existing legacy nodes or ambiguous parents require the named cutover.
"""
from pathlib import Path
import stat


class StatePathError(RuntimeError):
    """The old state path is not proved absent; mutation must not begin."""


def require_absent_legacy(room: Path, relative: Path) -> None:
    """Prove absence under a resolved room, refusing links and bad parents.

    Callers supply a fixed room-relative legacy path. A missing component
    proves absence only after all preceding components were real directories.
    This is a cooperating-writer check, not hostile same-user confinement.
    """
    if relative.is_absolute() or not relative.parts or any(p in (".", "..") for p in relative.parts):
        raise StatePathError("legacy state path is not room-relative")
    current = Path(room)
    for index, component in enumerate(relative.parts):
        current = current / component
        try:
            info = current.lstat()
        except FileNotFoundError:
            return
        except OSError:
            raise StatePathError("legacy state cannot be inspected; reviewed migration is required") from None
        if index == len(relative.parts) - 1:
            raise StatePathError("legacy state is present; reviewed migration is required")
        if not stat.S_ISDIR(info.st_mode):
            raise StatePathError("legacy state parent is not a real directory; reviewed migration is required")
