from __future__ import annotations

import dataclasses
import functools
import mimetypes
import os
import pathlib
import typing
import weakref

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, Response
from starlette.routing import BaseRoute, Mount, Route
from starlette.types import ASGIApp, Receive, Scope, Send

from bg_server._background_server import BackgroundServer
from bg_server._protocols import ProviderProtocol, ResourceManagerProtocol
from bg_server._util import hash_path, md5, StreamingFileResponse, ContentRange

__all__ = [
    "ContentProviderMount",
    "FileProviderMount",
    "Provider",
    "ProviderMount",
    "get_resources",
]

_RESOURCE_KEY = "_bg_server_resources"


@dataclasses.dataclass(frozen=True)
class ProviderMount:
    path: str
    routes: typing.Sequence[BaseRoute]
    manager: ResourceManagerProtocol


def mount_from_provider_mount(provider_mount: ProviderMount) -> Mount:
    """Create a Mount from a ProviderMount."""

    def middleware(app: ASGIApp):
        @functools.wraps(app)
        async def wrapped_app(scope: Scope, receive: Receive, send: Send):
            scope[_RESOURCE_KEY] = provider_mount.manager.resources
            await app(scope, receive, send)

        return wrapped_app

    return Mount(
        path=provider_mount.path,
        routes=provider_mount.routes,
        middleware=[(middleware, {})],  # type: ignore
    )


def get_resources(request: Request) -> typing.MutableMapping[str, typing.Any]:
    """Get the resources from the request scope."""
    return request.scope[_RESOURCE_KEY]


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


class ResourceProtocol(typing.Protocol):
    ...


def file_endpoint(request: Request):
    resources: typing.Mapping[str, FileResource] = get_resources(request)
    resource = resources[request.path_params["guid"]]

    media_type = mimetypes.guess_type(resource.path)[0] or "application/octet-stream"

    if "range" in request.headers:
        return StreamingFileResponse(
            path=resource.path,
            content_range=ContentRange.parse_header(request.headers["range"]),
            media_type=media_type,
        )

    return FileResponse(path=resource.path, media_type=media_type)


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

    def create(self, provider: ProviderProtocol, obj: str, **kwargs) -> ContentResource:
        resource = ContentResource(provider, obj, **kwargs)
        self.resources[resource.guid] = resource
        return resource

    def handles(self, obj: object) -> bool:
        return isinstance(obj, str)


def content_endpoint(request: Request):
    resources: typing.MutableMapping[str, ContentResource] = get_resources(request)
    resource = resources[request.path_params["guid"]]
    mime_type = mimetypes.guess_type(resource.guid)[0] or "text/plain"
    return Response(resource.contents, media_type=mime_type)


@dataclasses.dataclass
class ProviderContext:
    provider: ProviderProtocol
    scope: str

    @property
    def url(self) -> str:
        return f"{self.provider.url}{self.scope}"


class FileProviderMount(ProviderMount):
    def __init__(self, path: str = "/files"):
        super().__init__(
            path=path,
            routes=[Route("/{guid:path}", file_endpoint)],
            manager=FileResourceManager(),
        )


class ContentProviderMount(ProviderMount):
    def __init__(self, path: str = "/contents"):
        super().__init__(
            path=path,
            routes=[Route("/{guid:path}", content_endpoint)],
            manager=ContentResourceManager(),
        )


class Provider:
    """A server that provides resources to a client."""

    def __init__(
        self,
        routes: typing.Sequence[ProviderMount],
        allowed_origins: list[str] | None = None,
        proxy: bool = False,
    ):
        if allowed_origins is None:
            allowed_origins = ["*"]

        app = Starlette(routes=[mount_from_provider_mount(route) for route in routes])
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
        self._routes = routes

    def create(self, obj: object, **kwargs):
        self._bg_server.start()
        for ext in self._routes:
            if ext.manager.handles(obj):
                context = ProviderContext(self, ext.path)
                return ext.manager.create(context, obj, **kwargs)
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
