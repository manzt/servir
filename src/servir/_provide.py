from __future__ import annotations

import os
import pathlib
import typing
import weakref

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

from servir._background_server import BackgroundServer
from servir._protocols import TilesetProtocol
from servir._resources import (
    Resource,
    create_resource,
    create_resource_route,
)
from servir._tilesets import TilesetResource, TilesetType, create_tileset_route


class Provider(BackgroundServer):
    """A server that provides resources to a client."""

    _resources: typing.MutableMapping[str, Resource]
    _tilesets: typing.MutableMapping[str, TilesetResource[TilesetProtocol]]

    def __init__(self, proxy: bool = False):
        """Create a new Provider.

        Parameters
        ----------
        proxy : bool, optional
            Whether the url should be proxied for `jupyter-server-proxy` (default: False).
        """
        self._resources = weakref.WeakValueDictionary()
        self._tilesets = weakref.WeakValueDictionary()

        app = Starlette(
            routes=[
                create_tileset_route(self._tilesets),
                create_resource_route(self._resources),
            ],
        )
        # TODO: make this configurable?
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        self.proxy = proxy
        super().__init__(app)

    @property
    def url(self) -> str:
        """The URL for this provider.

        If proxy is True, the URL will be proxied for `jupyter-server-proxy`.

        If the environment variable `JUPYTERHUB_SERVICE_PREFIX` is set, the URL will be
        prefixed for JupyterHub.

        Returns
        -------
        str
            The URL for this provider.
        """
        if self.proxy:
            return f"/proxy/{self.port}"

        # https://github.com/yuvipanda/altair_data_server/blob/4d6ffcb19f864218c8d825ff2c95a1c8180585d0/altair_data_server/_altair_server.py#L73-L93
        if "JUPYTERHUB_SERVICE_PREFIX" in os.environ:
            urlprefix = os.environ["JUPYTERHUB_SERVICE_PREFIX"]
            return f"{urlprefix}/proxy/{self.port}"

        return f"http://localhost:{self.port}"

    @typing.overload
    def create(self, path: pathlib.Path | str, /, **kwargs: typing.Any) -> Resource:
        ...

    @typing.overload
    def create(
        self, tileset: TilesetType, /, **kwargs: typing.Any
    ) -> TilesetResource[TilesetType]:
        ...

    def create(
        self, x: pathlib.Path | str | TilesetType, /, **kwargs: typing.Any
    ) -> Resource | TilesetResource[TilesetType]:
        """Create a resource from a path or tileset.

        Parameters
        ----------
        x : pathlib.Path | str | TilesetProtocol
            The path or tileset to create a resource from.
        **kwargs
            Additional keyword arguments to pass to the resource constructor.

        Returns
        -------
        Resource | TilesetResource
            The resource.
        """
        resource: Resource | TilesetResource[TilesetProtocol]

        if not isinstance(x, (pathlib.Path, str)):
            resource = TilesetResource(x, provider=self, **kwargs)
            self._tilesets[resource.uid] = resource
        else:
            resource = create_resource(x, provider=self, **kwargs)
            self._resources[resource.guid] = resource

        self.start()
        return typing.cast(TilesetResource[TilesetType], resource)
