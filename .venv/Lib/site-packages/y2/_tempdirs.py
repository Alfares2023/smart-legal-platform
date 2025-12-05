import pathlib
import tempfile


def get_tempdir_root() -> pathlib.Path:
    return pathlib.Path(tempfile.gettempdir()) / "y2"


def mkdtemp(prefix: str | None = None) -> pathlib.Path:
    root = get_tempdir_root()
    root.mkdir(exist_ok=True)
    return pathlib.Path(tempfile.mkdtemp(prefix=prefix, dir=root))
