from __future__ import annotations

import pytest

from servir._tilesets import get_list


@pytest.mark.parametrize(
    "query, key, expected",
    [
        ("d=id1&d=id2&d=id3", "d", ["id1", "id2", "id3"]),
        ("d=1&e=2&d=3", "d", ["1", "3"]),
    ],
)
def test_get_list(query: str, key: str, expected: list[str]) -> None:
    assert get_list(query, key) == expected
