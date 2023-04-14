from __future__ import annotations

import functools
import itertools
import typing

from starlette.requests import Request
from starlette.responses import JSONResponse, PlainTextResponse, Response
from starlette.routing import Mount, Route
from starlette.types import ASGIApp

from bg_server._protocols import ProviderProtocol, TilesetProtocol

# HiGlass


MOUNT_PATH = "/tilesets/api/v1/"

class TilesetResource:
    def __init__(
        self, tileset: TilesetProtocol, provider: ProviderProtocol, uid: None | str = None
    ):
        self._tileset = tileset
        self._provider = provider
        self._uid = uid or str(id(tileset))

    @property
    def tileset(self) -> TilesetProtocol:
        return self._tileset

    @property
    def uid(self) -> str:
        return self._uid

    @property
    def server(self) -> str:
        return f"{self._provider.url}{MOUNT_PATH}"


def get_list(query: str, field: str) -> list[str]:
    """Parse chained query params into list.

    >>> get_list("d=id1&d=id2&d=id3", "d")
    ['id1', 'id2', 'id3']
    >>> get_list("d=1&e=2&d=3", "d")
    ['1', '3'].

    Parameters
    ----------
    query : str
        The query string. For example, "d=id1&d=id2&d=id3".
    field : str
        The field to extract. For example, "d".

    Returns
    -------
    list[str]
        The list of values for the given field. For example, ['id1', 'id2', 'id3'].
    """
    kv_tuples = [x.split("=") for x in query.split("&")]
    return [v for k, v in kv_tuples if k == field]


def tileset_info(request: Request, tilesets: typing.Mapping[str, TilesetResource]):
    uids = get_list(request.url.query, "d")
    info = {
        uid: tilesets[uid].tileset.info()
        if uid in tilesets
        else {"error": f"No such tileset with uid: {uid}"}
        for uid in uids
    }
    return JSONResponse(info)


def tiles(request: Request, tilesets: typing.Mapping[str, TilesetResource]):
    requested_tids = set(get_list(request.url.query, "d"))
    if not requested_tids:
        return JSONResponse({"error": "No tiles requested"}, 400)

    tiles: list = []
    for uid, tids in itertools.groupby(
        iterable=sorted(requested_tids), key=lambda tid: tid.split(".")[0]
    ):
        tileset_resource = tilesets.get(uid)
        if not tileset_resource:
            return JSONResponse(
                {"error": f"No tileset found for requested uid: {uid}"}, 400
            )
        tiles.extend(tileset_resource.tileset.tiles(list(tids)))
    data = {tid: tval for tid, tval in tiles}
    return JSONResponse(data)


def chromsizes(request: Request, tilesets: typing.Mapping[str, TilesetResource]):
    """Return chromsizes for given tileset id as TSV."""
    uid = request.query_params.get("id")
    if uid is None:
        return JSONResponse({"error": "No uid provided."}, 400)
    tileset_resource = tilesets[uid]
    info = tileset_resource.tileset.info()
    assert "chromsizes" in info, "No chromsizes in tileset info"
    return PlainTextResponse(
        "\n".join(f"{chrom}\t{size}" for chrom, size in info["chromsizes"])
    )


TilesetEndpoint = typing.Callable[
    [Request, typing.Mapping[str, TilesetResource]], Response
]


def create_tileset_route(
    tileset_resources: typing.Mapping[str, TilesetResource],
    scope_id: str = "tilesets",
) -> Mount:

    def middleware(app: ASGIApp):
        """Middleware to inject tileset resources into request scope."""
        @functools.wraps(app)
        async def wrapped_app(scope, receive, send):
            scope[scope_id] = tileset_resources
            await app(scope, receive, send)

        return wrapped_app


    def inject_tilesets(func: TilesetEndpoint) -> typing.Callable[[Request], Response]:
        """Inject tileset resources as secondrequest handler."""
        def wrapper(request: Request):
            return func(request, request.scope[scope_id])

        return wrapper


    return Mount(
        path=MOUNT_PATH,
        routes=[
            Route("/tileset_info/", inject_tilesets(tileset_info)),
            Route("/tiles/", inject_tilesets(tiles)),
            Route("/chrom-sizes/", inject_tilesets(chromsizes)),
        ],
        middleware=[(middleware, {})],  # type: ignore
    )
