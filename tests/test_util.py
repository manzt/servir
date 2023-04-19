from __future__ import annotations

import pathlib

import pytest
from starlette.responses import FileResponse, StreamingResponse

from servir._util import (
    ContentRange,
    create_file_response,
    create_resource_identifier,
    guess_media_type,
    md5,
    read_file_blocks,
)


@pytest.mark.parametrize(
    "header, expected",
    [
        ("bytes=0-499", ContentRange(0, 499)),
        ("bytes=500-", ContentRange(500, None)),
        ("bytes=500-999,", ContentRange(500, 999)),
        ("bytes=1-,", ContentRange(1, None)),
    ],
)
def test_content_range(header: str, expected: ContentRange) -> None:
    content_range = ContentRange.parse_header(header)
    assert content_range == expected


@pytest.mark.parametrize(
    "header",
    [
        ("bytes=500-999, 501-399"),
        ("bytes=0-100, -399"),
    ],
)
def test_unsupported_content_range(header: str) -> None:
    with pytest.raises(ValueError):
        ContentRange.parse_header(header)


def test_md5() -> None:
    assert md5(b"test") == md5("test")


@pytest.mark.parametrize(
    "start, end, expected",
    [
        (0, 4, b"test"),
        (1, 4, b"est"),
        (4, 4, b""),
    ],
)
def test_read_file_blocks(
    tmp_path: pathlib.Path, start: int, end: int, expected: bytes
) -> None:
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    assert b"".join(read_file_blocks(test_file, start, end)) == expected


@pytest.mark.parametrize(
    "path, expected",
    [
        ("none", "application/octet-stream"),
        ("data.txt", "text/plain"),
        ("data.json", "application/json"),
    ],
)
def test_guess_media_type(path: str, expected: str) -> None:
    assert guess_media_type(path) == expected


@pytest.mark.parametrize(
    "range_header, expected",
    [
        ("bytes=0-499", StreamingResponse),
        (None, FileResponse),
    ],
)
def test_create_file_response(
    range_header: str, expected: type[FileResponse], tmp_path: pathlib.Path
) -> None:
    path = tmp_path / "data.txt"
    path.write_text("test")
    file_response = create_file_response(path, range_header)
    assert isinstance(file_response, expected)


def test_create_resource_identifier() -> None:
    identifer = create_resource_identifier("hello, world", "data.txt")
    assert identifer.endswith("-data.txt")
