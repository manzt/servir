from __future__ import annotations

import typing

__all__ = [
    "ProviderProtocol",
    "TilesetProtocol",
]


class ProviderProtocol(typing.Protocol):
    @property
    def url(self) -> str:
        ...


class TilesetProtocol(typing.Protocol):
    def tiles(self, tile_ids: typing.Sequence[str]) -> list[typing.Any]:
        ...

    def info(self) -> dict[str, typing.Any]:
        ...
