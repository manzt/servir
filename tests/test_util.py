import pathlib

import pytest

from bg_server._util import ContentRange, md5, read_file_blocks


@pytest.mark.parametrize(
    "header, expected",
    [
        ("bytes=0-499", ContentRange(0, 499)),
        ("bytes=500-", ContentRange(500, None)),
        ("bytes=500-999,", ContentRange(500, 999)),
        ("bytes=1-,", ContentRange(1, None)),
    ],
)
def test_content_range(header: str, expected: tuple[int, int]):
    content_range = ContentRange.parse_header(header)
    assert content_range == expected


@pytest.mark.parametrize(
    "header",
    [
        ("bytes=500-999, 501-399"),
        ("bytes=0-100, -399"),
    ],
)
def test_unsupported_content_range(header: str):
    with pytest.raises(ValueError):
        ContentRange.parse_header(header)

def test_md5():
    assert md5(b"test") == md5("test")

@pytest.mark.parametrize(
    "start, end, expected",
    [
        (0, 4, b"test"),
        (1, 4, b"est"),
        (4, 4, b""),
    ],
)
def test_read_file_blocks(tmp_path: pathlib.Path, start: int, end: int, expected: bytes):
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    assert b"".join(read_file_blocks(test_file, start, end)) == expected
