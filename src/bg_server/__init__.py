try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version  # type: ignore

try:
    __version__ = version("bg-server")
except PackageNotFoundError:
    __version__ = "uninstalled"

from bg_server._provide import Provider, FileProviderMount # noqa
