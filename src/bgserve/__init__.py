"""bgserve provides a simple way to serve static files and dynamic content."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bgserve")
except PackageNotFoundError:
    __version__ = "uninstalled"

from bgserve._provide import Provider as Provider
