from __future__ import annotations

import dataclasses
import os
import weakref
from typing import Generic, MutableMapping, Protocol, Sequence, TypeVar

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware
from starlette.routing import Route

from bg_server._background_server import BackgroundServer

ResourceT = TypeVar("ResourceT")

class ResourceHandler(Protocol, Generic[ResourceT]):
    """A handler for a specific type of resource."""

    def create_route(self, context: MutableMapping[str, ResourceT]) -> Route:
        """Create a route for resources of this type."""
        ...

    def handles(self, obj: object) -> bool:
        """Return whether this handler can handle the object."""
        ...

    def pathname_for(self, resource: ResourceT) -> str:
        """Return the pathname for the resource on the server."""
        ...

    def guid_for(self, resource: ResourceT) -> str:
        """Return a unique identifier for the resource."""
        ...

class ProviderContext:
    """Wraps a given resource with its provider."""

    def __init__(self, provider: Provider, pathname: str):
        self._provider = provider
        self._pathname = pathname

    @property
    def url(self) -> str:
        return f"{self._provider.url}/{self._pathname.lstrip('/')}"


@dataclasses.dataclass
class ResourceManager(Generic[ResourceT]):
    handler: ResourceHandler[ResourceT]
    resources: MutableMapping[str, ResourceT]


class Provider:
    """A server that provides resources to a client."""

    def __init__(
        self,
        handlers: Sequence[ResourceHandler],
        allowed_origins: list[str] | None = None,
        proxy: bool = False,
    ):

        if allowed_origins is None:
            allowed_origins = ["*"]

        self._managers = [
            ResourceManager(handler, weakref.WeakValueDictionary())
            for handler in handlers
        ]

        app = Starlette(
            routes=[m.handler.create_route(m.resources) for m in self._managers]
        )

        # configure cors
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

    def add_resource(self, resource: object) -> ProviderContext:
        for manager in self._managers:
            if manager.handler.handles(resource):
                guid = manager.handler.guid_for(resource)
                manager.resources[guid] = resource
                break
        else:
            raise ValueError(f"No handler for {resource} of type {type(resource)}")

        self._bg_server.start()
        return ProviderContext(self, manager.handler.pathname_for(resource))

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

