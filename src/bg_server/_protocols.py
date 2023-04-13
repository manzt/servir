from __future__ import annotations

import typing

ResourceT = typing.TypeVar("ResourceT")


class ProviderProtocol(typing.Protocol):
    @property
    def url(self) -> str:
        ...


class ResourceManagerProtocol(typing.Protocol, typing.Generic[ResourceT]):
    resources: typing.MutableMapping[str, ResourceT]

    def create(
        self,
        provider: ProviderProtocol,
        obj: object,
        **kwargs,
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
