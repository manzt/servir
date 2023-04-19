from __future__ import annotations

import typing

__all__ = [
    "ProviderProtocol",
    "TilesetProtocol",
]


class ProviderProtocol(typing.Protocol):
    """A protocol for a provider that can serve resources."""

    @property
    def url(self) -> str:
        """The URL for this provider."""
        ...


class TilesetProtocol(typing.Protocol):
    """Represents a HiGlass Tileset."""

    @property
    def uid(self) -> str:
        """The unique identifier for this tileset."""
        ...

    def tiles(self, tile_ids: typing.Sequence[str]) -> list[typing.Any]:
        """Get the tiles for the given tile IDs.

        Parameters
        ----------
        tile_ids : list[str]
            The tile IDs to get.

        Returns
        -------
        list[typing.Any]
            The tiles.
        """
        ...

    def info(self) -> dict[str, typing.Any]:
        """Get the tileset info for this tileset.

        Returns
        -------
        dict[str, typing.Any]
            The tileset info.
        """
        ...
