from __future__ import annotations

import functools
import typing

from starlette.types import ASGIApp, Receive, Scope, Send

ResourceT = typing.TypeVar("ResourceT")


class ProviderProtocol(typing.Protocol):

    @property
    def url(self) -> str: ...


class ResourceManagerProtocol(typing.Protocol, typing.Generic[ResourceT]):
    resources: typing.MutableMapping[str, ResourceT]

    def create(
        self, provider: ProviderProtocol, obj: object, **kwargs,
    ) -> ResourceT:
        """Create a resource from an object.

        Parameters
        ----------
        provider : ProviderProtocol
            The provider that will serve the resource.

        obj : object
            The object to create the resource from.

        Returns
        -------
        ResourceT
            The created server resource.
        """
        ...

    def handles(self, obj: object) -> bool:
        """Check if the manager can handle an object.

        Parameters
        ----------
        obj : object
            The object to check.

        Returns
        -------
        bool
            Whether the manager can handle the object.
        """
        ...


def resource_middleware(resources: typing.MutableMapping[str, typing.Any]):
    def asgi_decorator(app: ASGIApp):

        @functools.wraps(app)
        async def wrapped_app(scope: Scope, receive: Receive, send: Send):
            scope["resources"] = resources
            await app(scope, receive, send)

        return wrapped_app

    return asgi_decorator


def get_resources(scope: Scope) -> typing.MutableMapping[str, typing.Any]:
    return scope["resources"]
