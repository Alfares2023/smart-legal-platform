import shutil

from y2._tempdirs import get_tempdir_root
from y2._console import console


def clean() -> None:
    """Clean up temp files used by 2."""
    root = get_tempdir_root()
    if not root.exists():
        return
    console.print(f"Deleting {root!s}")
    shutil.rmtree(root)
