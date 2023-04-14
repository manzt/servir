from __future__ import annotations

import functools
import os
import pathlib
import typing
import weakref

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import CORSMiddleware

from bg_server._background_server import BackgroundServer
from bg_server._resources import (
    Resource,
    create_resource,
    create_resource_route,
)
from bg_server._tilesets import TilesetProtocol, TilesetResource, create_tileset_route


def _create_app(routes: list[Route]) -> Starlette:

class Provider(BackgroundServer):
    """A server that provides resources to a client."""

    def __init__(
        self,
        allowed_origins: list[str] | None = None,
        proxy: bool = False,
    ):
        self._resources: typing.MutableMapping[
            str, Resource
        ] = weakref.WeakValueDictionary()
        self._tilesets: typing.MutableMapping[
            str, TilesetResource
        ] = weakref.WeakValueDictionary()

        app = Starlette(
            routes=[
                create_tileset_route(self._tilesets),
                create_resource_route(self._resources),
            ]
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=allowed_origins or ["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.proxy = proxy
        super().__init__(app)

    @property
    def url(self) -> str:
        if self.proxy:
            return f"/proxy/{self.port}"

        # https://github.com/yuvipanda/altair_data_server/blob/4d6ffcb19f864218c8d825ff2c95a1c8180585d0/altair_data_server/_altair_server.py#L73-L93
        if "JUPYTERHUB_SERVICE_PREFIX" in os.environ:
            urlprefix = os.environ["JUPYTERHUB_SERVICE_PREFIX"]
            return f"{urlprefix}/proxy/{self.port}"

        return f"http://localhost:{self.port}"

    @typing.overload
    def create(self, path: pathlib.Path | str, /, **kwargs) -> Resource:
        ...

    @typing.overload
    def create(self, tileset: TilesetProtocol, /, **kwargs) -> TilesetResource:
        ...

    def create(
        self, x: pathlib.Path | str | TilesetProtocol, /, **kwargs
    ) -> Resource | TilesetResource:
        self.start()

        if not isinstance(x, (pathlib.Path, str)):
            resource = TilesetResource(x, provider=self, **kwargs)
            self._tilesets[resource.uid] = resource
            return resource

        resource = create_resource(x, provider=self, **kwargs)
        self._resources[resource.guid] = resource
        return resource
