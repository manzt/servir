"""bgserve provides a simple way to serve static files and dynamic content."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("bgserve")
except PackageNotFoundError:
    __version__ = "uninstalled"

from bgserve._provide import Provider
from bgserve._resources import Resource
from bgserve._tilesets import TilesetResource

__all__ = ["Provider", "Resource", "TilesetResource", "__version__"]
