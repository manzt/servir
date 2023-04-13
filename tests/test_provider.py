import pathlib
import urllib.request as urllib

import pytest

from bg_server._provide import FileResourceManager, Provider, ProviderMount, file_route


def test_no_handler():
    provider = Provider(extensions=[])
    with pytest.raises(ValueError):
        provider.create("foo")


def test_handles_files(tmp_path: pathlib.Path):
    with open(tmp_path / "hello.txt", "w") as f:
        f.write("hello, world")

    provider = Provider([
        ProviderMount("/files", routes=[file_route], manager=FileResourceManager()),
    ])
    server_resource = provider.create(tmp_path / "hello.txt")
    print(server_resource.url)

    request = urllib.Request(server_resource.url)
    with urllib.urlopen(request) as response:
        assert response.read() == b"hello, world"

