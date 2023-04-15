from __future__ import annotations

import abc
import pathlib
import typing
import uuid

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from bg_server._util import (
    create_file_response,
    create_resource_identifier,
    guess_media_type,
)


class ProviderProtocol(typing.Protocol):
    @property
    def url(self) -> str:
        ...


class Resource(metaclass=abc.ABCMeta):
    def __init__(
        self,
        provider: ProviderProtocol,
        headers: None | dict[str, str] = None,
    ):
        self.headers = headers or {}
        self._provider = provider
        self._guid = uuid.uuid4().hex

    @property
    def guid(self) -> str:
        return self._guid

    @property
    def url(self) -> str:
        return f"{self._provider.url}/resources/{self.guid}"

    @abc.abstractmethod
    def get(self, request: Request, **kwargs) -> typing.Awaitable[Response]:
        ...


class FileResource(Resource):
    def __init__(self, path: pathlib.Path, **kwargs):
        super().__init__(**kwargs)
        assert path.is_file(), "Path must be a file"
        self._path = path
        self._guid = create_resource_identifier(
            data=path.resolve().as_posix(), id=path.name
        )

    def get(self, request: Request) -> Response:
        response = create_file_response(self._path, request.headers.get("range"))
        response.headers.update(self.headers)
        return response


class DirectoryResource(Resource):
    def __init__(self, path: pathlib.Path, **kwargs):
        super().__init__(**kwargs)
        assert path.is_dir(), "Path must be a directory"
        self._path = path
        self._guid = create_resource_identifier(
            data=path.resolve().as_posix(),
            id=path.name.lstrip("/"),
        )

    def get(self, request: Request) -> Response:
        full_path: str = request.path_params["path"]
        resolved = self._path / full_path.replace(self._guid, "").lstrip("/")
        response = create_file_response(resolved, request.headers.get("range"))
        response.headers.update(self.headers)
        return response


class ContentResource(Resource):
    def __init__(self, content: str | bytes, extension: None | str = None, **kwargs):
        super().__init__(**kwargs)
        self._content = content
        if extension is None:
            extension = ".txt" if isinstance(content, str) else ".bin"
        self._guid = create_resource_identifier(data=content, id=f"content{extension}")

    def get(self, _: Request) -> Response:
        return Response(
            content=self._content,
            media_type=guess_media_type(self._guid),
            headers=self.headers.copy(),
        )


def create_resource_route(resources: typing.Mapping[str, Resource]) -> Mount:
    def endpoint(request: Request) -> typing.Awaitable[Response]:
        path = request.path_params["path"]
        guid = path.split("/")[0]
        return resources[guid].get(request)

    return Mount(
        path="/resources",
        routes=[
            Route("/{path:path}", endpoint, methods=["GET", "HEAD"]),
        ],
    )


def create_resource(
    x: pathlib.Path | str, provider: ProviderProtocol, **kwargs
) -> Resource:
    if isinstance(x, str):
        return ContentResource(x, provider=provider, **kwargs)
    if isinstance(x, pathlib.Path) and x.is_file():
        return FileResource(x, provider=provider, **kwargs)
    if isinstance(x, pathlib.Path) and x.is_dir():
        return DirectoryResource(x, provider=provider, **kwargs)
    raise TypeError(f"Unsupported type: {type(x)}")
