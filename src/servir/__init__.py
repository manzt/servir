"""servir provides a simple way to serve static files and dynamic content."""

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("servir")
except PackageNotFoundError:
    __version__ = "uninstalled"

from servir._provide import Provider
from servir._resources import Resource
from servir._tilesets import TilesetResource

__all__ = ["Provider", "Resource", "TilesetResource", "__version__"]
