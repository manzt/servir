from __future__ import annotations

import abc
import pathlib
import typing
import uuid

from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Mount, Route

from servir._protocols import ProviderProtocol
from servir._util import (
    create_file_response,
    create_resource_identifier,
    guess_media_type,
)

__all__ = [
    "Resource",
    "FileResource",
    "DirectoryResource",
    "ContentResource",
    "create_resource_route",
    "create_resource",
]


class Resource(metaclass=abc.ABCMeta):
    """A resource that can be served by a provider."""

    def __init__(
        self,
        provider: ProviderProtocol,
        headers: None | dict[str, str] = None,
    ):
        """Create a new Resource.

        Parameters
        ----------
        provider : ProviderProtocol
            The provider that will serve this resource.
        headers : dict[str, str], optional
            Additional headers to include in the response.
        """
        self.headers = headers or {}
        self._provider = provider
        self._guid = uuid.uuid4().hex

    @property
    def guid(self) -> str:
        """The unique identifier for this resource."""
        return self._guid

    @property
    def url(self) -> str:
        """The URL for this resource."""
        return f"{self._provider.url}/resources/{self.guid}"

    @abc.abstractmethod
    def get(self, request: Request) -> Response:
        """Get the resource.

        Parameters
        ----------
        request : Request
            The request to handle.

        Returns
        -------
        Response
            The response to send.
        """
        ...


class FileResource(Resource):
    def __init__(self, path: pathlib.Path, **kwargs: typing.Any):
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
    """Serve a directory as a resource."""

    def __init__(self, path: pathlib.Path, **kwargs: typing.Any):
        """Create a new DirectoryResource.

        Parameters
        ----------
        path : pathlib.Path
            The path to the directory to serve.

        kwargs : dict
            Additional keyword arguments to pass to the Resource constructor.

        Raises
        ------
        ValueError
            If the path is not a directory.
        """
        super().__init__(**kwargs)

        if not path.is_dir():
            raise ValueError("Path must be a directory")

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
    """Serve a string or bytes as a resource."""

    def __init__(
        self, content: str | bytes, extension: None | str = None, **kwargs: typing.Any
    ):
        """Create a new ContentResource.

        Parameters
        ----------
        content : str | bytes
            The content to serve.
        extension : str, optional
            The extension to use for the resource identifier.
        kwargs : dict
            Additional keyword arguments to pass to the Resource constructor.
        """
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
    """Create a route for serving resources.

    Parameters
    ----------
    resources : typing.Mapping[str, Resource]
        A mapping of resource identifiers to resources.

    Returns
    -------
    Mount
        A route for serving resources.
    """

    def endpoint(request: Request) -> Response:
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
    x: pathlib.Path | str, provider: ProviderProtocol, **kwargs: typing.Any
) -> Resource:
    """Create a resource from a path or string.

    Parameters
    ----------
    x : pathlib.Path | str
        The path or string to create a resource from.
    provider : ProviderProtocol
        The provider that will serve the resource.
    kwargs : dict
        Additional keyword arguments to pass to the Resource constructor.

    Returns
    -------
    Resource
        The created resource.
    """
    if isinstance(x, str):
        return ContentResource(x, provider=provider, **kwargs)
    if isinstance(x, pathlib.Path) and x.is_file():
        return FileResource(x, provider=provider, **kwargs)
    if isinstance(x, pathlib.Path) and x.is_dir():
        return DirectoryResource(x, provider=provider, **kwargs)
    raise TypeError(f"Unsupported type: {type(x)}")
