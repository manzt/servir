from __future__ import annotations
import dataclasses

import hashlib
import mimetypes
import os
import pathlib
import typing
import weakref

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, Response, StreamingResponse
from starlette.routing import BaseRoute, Mount, Route

from bg_server._background_server import BackgroundServer
from bg_server._protocols import (
    ProviderProtocol,
    ResourceManagerProtocol,
    get_resources,
    resource_middleware,
)

__all__ = [
    "FileResource",
    "FileResourceManager",
    "file_route",
    "ContentResource",
    "ContentResourceManager",
    "content_route",
]


def md5(data: str | bytes) -> str:
    """Hash a string to a string.

    This is used to generate a unique identifier for a string resource.

    Parameters
    ----------
    string : str
        The string to hash.

    Returns
    -------
    str :
        A unique identifier for the string.
    """
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).hexdigest()


def hash_path(path: pathlib.Path) -> str:
    """Hash a path to a string.

    This is used to generate a unique identifier for a file resource.

    Parameters
    ----------
    path : pathlib.Path
        The path to hash.

    Returns
    -------
    str :
        A unique identifier for the path.
    """
    return md5(path.resolve().as_posix()) + path.suffix


# adapted from https://gist.github.com/tombulled/712fd8e19ed0618c5f9f7d5f5f543782
def ranged(
    file: typing.IO[bytes],
    start: int = 0,
    end: None | int = None,
    block_size: int = 65535,
) -> typing.Generator[bytes, None, None]:
    """Read content range as generator from file object.

    Parameters
    ----------
    file : IO[bytes]
        The file object to read from.
    start : int, optional
        The start of the byte-range (default 0)
    end : None | int, optional
        The end of the desired byte-range. If None, the end of the file is assumed.
    block_size : int, optional
        The block size to read, by default 65535

    Yields
    ------
    bytes
        The content range.
    """
    consumed = 0
    file.seek(start)

    while True:
        data_length = min(block_size, end - start - consumed) if end else block_size
        if data_length <= 0:
            break
        data = file.read(data_length)
        if not data:
            break
        consumed += data_length
        yield data

    if hasattr(file, "close"):
        file.close()


def parse_content_range(content_range: str, file_size: int) -> tuple[int, int]:
    """Parse 'Range' header into integer interval.

    Parameters
    ----------
    content_range : str
        The 'Range' header.
    file_size : int
        The size of the file.

    Returns
    -------
    tuple[int, int]
        The start and end of the byte-range.
    """
    content_range = content_range.strip().lower()
    content_ranges = content_range.split("=")[-1]
    range_start, range_end, *_ = map(str.strip, (content_ranges + "-").split("-"))
    return (
        max(0, int(range_start)) if range_start else 0,
        min(file_size - 1, int(range_end)) if range_end else file_size - 1,
    )


class FileResource:
    def __init__(self, provider: ProviderProtocol, path: pathlib.Path):
        self.provider = provider
        self.path = path
        self.guid = hash_path(path)

    @property
    def url(self) -> str:
        return f"{self.provider.url}/{self.guid}"


class FileResourceManager(ResourceManagerProtocol[FileResource]):
    def __init__(self):
        self.resources = weakref.WeakValueDictionary()

    def create(
        self, provider: ProviderProtocol, obj: pathlib.Path, **kwargs
    ) -> FileResource:
        resource = FileResource(provider, obj, **kwargs)
        self.resources[resource.guid] = resource
        return resource

    def handles(self, obj: object) -> bool:
        return isinstance(obj, pathlib.Path)


def file_endpoint(request: Request):
    resources: typing.MutableMapping[str, FileResource] = get_resources(request.scope)
    resource = resources[request.path_params["guid"]]

    path = resource.path
    media_type = mimetypes.guess_type(path)[0] or "application/octet-stream"
    content_range = request.headers.get("range")

    if content_range is not None:
        file = path.open("rb")
        file_size = path.stat().st_size
        range_start, range_end = parse_content_range(content_range, file_size)
        content_length = (range_end - range_start) + 1
        file = ranged(file, start=range_start, end=range_end + 1)

        return StreamingResponse(
            content=file,
            media_type=media_type,
            status_code=206,
            headers={
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
                "range": f"bytes {range_start}-{range_end}/{file_size}",
            },
        )

    return FileResponse(path, media_type=media_type)


file_route = Route("/{guid:path}", file_endpoint)


class ContentResource:
    def __init__(
        self, provider: ProviderProtocol, contents: str | bytes, extension: str = ""
    ):
        self.provider = provider
        self.contents = contents
        self.guid = md5(contents) + (extension or "")

    @property
    def url(self) -> str:
        return f"{self.provider.url}/{self.guid}"


class ContentResourceManager(ResourceManagerProtocol[ContentResource]):
    def __init__(self):
        self.resources = weakref.WeakValueDictionary()

    def create(
        self, provider: ProviderProtocol, obj: str | bytes, **kwargs
    ) -> ContentResource:
        resource = ContentResource(provider, obj, **kwargs)
        self.resources[resource.guid] = resource
        return resource

    def handles(self, obj: object) -> bool:
        return isinstance(obj, (str, bytes))


def content_endpoint(request: Request):
    resources: typing.MutableMapping[str, ContentResource] = get_resources(request.scope)
    resource = resources[request.path_params["guid"]]
    mime_type = mimetypes.guess_type(resource.guid)[0]
    if mime_type is None:
        mime_type = (
            "application/octet-stream"
            if isinstance(resource.contents, bytes)
            else "text/plain"
        )
    return Response(resource.contents, media_type=mime_type)


content_route = Route("/{guid:path}", content_endpoint)


@dataclasses.dataclass
class ProviderContext:
    provider: ProviderProtocol
    scope: str

    @property
    def url(self) -> str:
        return f"{self.provider.url}{self.scope}"

class Provider:
    """A server that provides resources to a client."""

    def __init__(
        self,
        extensions: typing.Sequence[ProviderMount],
        allowed_origins: list[str] | None = None,
        proxy: bool = False,
    ):
        if allowed_origins is None:
            allowed_origins = ["*"]

        app = Starlette(
            routes=[
                Mount(
                    path=m.path,
                    routes=m.routes,
                    middleware=[(resource_middleware(m.manager.resources), {})],  # type: ignore
                )
                for m in extensions
            ]
        )
        if allowed_origins:
            app.add_middleware(
                CORSMiddleware,
                allow_origins=allowed_origins,
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
            )

        self._proxy = proxy
        self._bg_server = BackgroundServer(app)
        self._extensions = extensions

    def create(self, obj: object):
        for ext in self._extensions:
            if ext.manager.handles(obj):
                self._bg_server.start()
                return ext.manager.create(ProviderContext(self, ext.path), obj)
        raise ValueError(f"Cannot create resource for {obj}")

    @property
    def url(self) -> str:
        port = self._bg_server.port

        if self._proxy:
            return f"/proxy/{port}"

        # https://github.com/yuvipanda/altair_data_server/blob/4d6ffcb19f864218c8d825ff2c95a1c8180585d0/altair_data_server/_altair_server.py#L73-L93
        if "JUPYTERHUB_SERVICE_PREFIX" in os.environ:
            urlprefix = os.environ["JUPYTERHUB_SERVICE_PREFIX"]
            return f"{urlprefix}/proxy/{port}"

        return f"http://localhost:{port}"


@dataclasses.dataclass
class ProviderMount:
    path: str
    routes: typing.Sequence[BaseRoute]
    manager: ResourceManagerProtocol


class FileProviderMount(ProviderMount):
    path: str = "/files"
    routes: typing.Sequence[BaseRoute] = [file_route]
    manager: ResourceManagerProtocol = dataclasses.field(
        default_factory=FileResourceManager
    )
