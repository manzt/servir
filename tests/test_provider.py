from __future__ import annotations

import json
import pathlib

import requests

from bg_server._provide import Provider


def test_files(tmp_path: pathlib.Path):
    with open(tmp_path / "hello.txt", "w") as f:
        f.write("hello, world")

    provider = Provider()

    server_resource = provider.create(tmp_path / "hello.txt")
    response = requests.get(server_resource.url)
    assert response.text == "hello, world"
    assert "text/plain" in response.headers["Content-Type"]

    response = requests.get(provider.url + "/foo.txt")
    assert response.status_code == 404


def test_file_content_type_json(tmp_path: pathlib.Path):
    data = {"hello": "world"}

    with open(tmp_path / "hello.json", "w") as f:
        json.dump(data, f)

    provider = Provider()

    server_resource = provider.create(tmp_path / "hello.json")
    response = requests.get(server_resource.url)
    assert response.json() == data
    assert "application/json" in response.headers["Content-Type"]


def test_file_content_type_csv(tmp_path: pathlib.Path):
    path = tmp_path / "data.csv"
    path.write_text("a,b,c\n1,2,3\n4,5,6")

    provider = Provider()
    server_resource = provider.create(path)
    response = requests.get(server_resource.url)
    assert response.text == path.read_text()
    assert "text/csv" in response.headers["Content-Type"]


def test_content():
    content = "hello, world"
    provider = Provider()
    str_resource = provider.create(content)
    response = requests.get(str_resource.url)
    assert response.text == content
    assert "text/plain" in response.headers["Content-Type"]


def test_content_explicit_extension():
    data = "a,b,c,\n1,2,3,\n4,5,6"
    provider = Provider()

    content_resource = provider.create(data, extension=".csv")

    response = requests.get(content_resource.url)
    assert response.text == data
    assert "text/csv" in response.headers["Content-Type"]


def test_directory_resource(tmp_path: pathlib.Path):
    provider = Provider()

    root = tmp_path / "data_dir"
    root.mkdir()
    (root / "hello.txt").write_text("hello, world")
    (root / "nested_dir").mkdir()
    (root / "nested_dir" / "foo.txt").write_text("foo")

    server_resource = provider.create(root)
    print(server_resource.url)

    response = requests.get(server_resource.url + "/hello.txt")
    assert response.text == "hello, world"

    response = requests.get(server_resource.url + "/nested_dir/foo.txt")
    assert response.text == "foo"
