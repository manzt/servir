from __future__ import annotations

import hashlib
import mimetypes
import pathlib
from typing import IO, Generator, MutableMapping

from starlette.requests import Request
from starlette.responses import FileResponse, StreamingResponse
from starlette.routing import Mount, Route


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
    str_path = str(path.absolute())
    return hashlib.md5(str_path.encode()).hexdigest() + path.suffix


# adapted from https://gist.github.com/tombulled/712fd8e19ed0618c5f9f7d5f5f543782
def ranged(
    file: IO[bytes], start: int = 0, end: None | int = None, block_size: int = 65535
) -> Generator[bytes, None, None]:
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


class FileResourceHandler:
    def __init__(self, scope: str = "files"):
        self._scope = scope

    def handles(self, resource: object) -> bool:
        return isinstance(resource, pathlib.Path)

    def pathname_for(self, resource: pathlib.Path) -> str:
        return f"/{self._scope}/{self.guid_for(resource)}"

    def guid_for(self, resource: pathlib.Path) -> str:
        return hash_path(resource)

    def create_route(self, resources: MutableMapping[str, pathlib.Path]) -> Mount:
        def route(request: Request):
            path = resources[request.path_params["guid"]]
            media_type, _ = mimetypes.guess_type(path)
            media_type = media_type or "application/octet-stream"

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

        return Mount(f"/{self._scope}", routes=[Route("/{guid:path}", route)])
