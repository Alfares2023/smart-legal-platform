from importlib import metadata
import sys


def pv(package: str, /) -> None:
    """Print the installed PyPI package's version."""
    try:
        print(metadata.version(package))
    except metadata.PackageNotFoundError:
        print(f"No such package: {package}", file=sys.stderr)
