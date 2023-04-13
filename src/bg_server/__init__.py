"""bg_server provides a simple way to serve static files and dynamic content."""

try:
    from importlib.metadata import PackageNotFoundError, version
except ImportError:
    from importlib_metadata import PackageNotFoundError, version  # type: ignore

try:
    __version__ = version("bg-server")
except PackageNotFoundError:
    __version__ = "uninstalled"

from bg_server._provide import (
    ContentProviderMount as ContentProviderMount,
)
from bg_server._provide import (
    FileProviderMount as FileProviderMount,
)
from bg_server._provide import (
    Provider as Provider,
)
from bg_server._provide import (
    ProviderMount as ProviderMount,
)
from bg_server._provide import (
    get_resources as get_resources,
)
