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
    data = "a,b,c\n1,2,3\n4,5,6"

    with open(tmp_path / "data.csv", "w") as f:
        f.write(data)

    provider = Provider()
    server_resource = provider.create(tmp_path / "data.csv")
    response = requests.get(server_resource.url)
    assert response.text == data
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
