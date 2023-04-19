from __future__ import annotations

import dataclasses
import hashlib
import mimetypes
import pathlib
import re
import typing

from starlette.responses import FileResponse, StreamingResponse


def md5(data: str | bytes) -> str:
    """Generate a unique identifier for a string or bytes.

    Parameters
    ----------
    string : str
        The string to hash.

    Returns
    -------
    str :
        A unique identifier for the string.
    """
    if isinstance(data, str):
        data = data.encode()
    return hashlib.md5(data).hexdigest()


def create_resource_identifier(data: str | bytes, id: str) -> str:
    """Create a unique identifier for a string or bytes.

    Parameters
    ----------
    data : str | bytes
        The string or bytes to hash.
    id : str
        The identifier for the data.

    Returns
    -------
    str :
        A unique identifier for the string or bytes.
    """
    return f"{md5(data)[:7]}-{id}"


def read_file_blocks(
    path: pathlib.Path,
    start: int = 0,
    end: None | int = None,
    block_size: int = 65535,
) -> typing.Iterator[bytes]:
    """Read content range as generator from file object.

    Adapted from https://gist.github.com/tombulled/712fd8e19ed0618c5f9f7d5f5f543782

    Parameters
    ----------
    path : pathlib.Path
        The path to the file.
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

    file = path.open("rb")
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


@dataclasses.dataclass(frozen=True)
class ContentRange:
    start: int
    end: int | None

    @classmethod
    def parse_header(cls, header: str) -> ContentRange:
        """Parse 'Range' header into integer interval.

        Does not support multiple ranges.

        Parameters
        ----------
        content_range : str
            The 'Range' header.

        Returns
        -------
        tuple[int, int]
            The start and end of the byte-range.
        """
        content_range_header = header.strip().lower()

        match = re.match(r"^bytes=(\d+)-(\d+)?,?$", content_range_header)

        if not match:
            raise ValueError("Invalid 'Range' header. Must be of the form 'bytes=0-499'.")

        range_start, range_end = match.groups()
        return cls(
            start=int(range_start),
            end=int(range_end) if range_end else None,
        )


def create_streaming_file_response(
    path: pathlib.Path,
    content_range: ContentRange | None = None,
    media_type: str | None = None,
    headers: None | typing.Mapping[str, str] = None,
) -> StreamingResponse:
    file_size = path.stat().st_size

    if not content_range:
        start, end = (0, file_size - 1)
        status_code = 200
        headers = {
            **(headers or {}),
            "Content-Length": str(file_size),
        }
    else:
        status_code = 206
        start, end = (content_range.start, content_range.end or file_size - 1)
        headers = {
            **(headers or {}),
            "Content-Length": str((end - start) + 1),
            "Accept-Ranges": "bytes",
            "range": f"bytes {start}-{end}/{file_size}",
        }

    return StreamingResponse(
        content=read_file_blocks(path, start=start, end=end + 1),
        media_type=media_type,
        status_code=status_code,
        headers=headers,
    )


def create_file_response(
    path: pathlib.Path,
    content_range_header: str | None = None,
) -> FileResponse | StreamingResponse:
    media_type = guess_media_type(path)
    if content_range_header:
        content_range = ContentRange.parse_header(content_range_header)
        return create_streaming_file_response(
            path=path,
            content_range=content_range,
            media_type=media_type,
        )
    return FileResponse(path=path, media_type=media_type)


def guess_media_type(path: str | pathlib.Path) -> str:
    """Guess the media type of a file.

    Parameters
    ----------
    path : pathlib.Path
        The path to the file.

    Returns
    -------
    str
        The media type.
    """
    return mimetypes.guess_type(path)[0] or "application/octet-stream"
