<a id="servir"></a>

### servir

servir provides a simple way to serve static files and dynamic content.

<a id="servir._provide"></a>

### servir.\_provide

<a id="servir._provide.Provider"></a>

#### Provider

```python
class Provider(BackgroundServer)
```

A server that provides resources to a client.

<a id="servir._provide.Provider.__init__"></a>

##### \_\_init\_\_

```python
def __init__(proxy: bool = False)
```

Create a new Provider.

Parameters
----------
proxy : bool, optional
    Whether the url should be proxied for `jupyter-server-proxy` (default: False).

<a id="servir._provide.Provider.url"></a>

##### url

```python
@property
def url() -> str
```

The URL for this provider.

If proxy is True, the URL will be proxied for `jupyter-server-proxy`.

If the environment variable `JUPYTERHUB_SERVICE_PREFIX` is set, the URL will be
prefixed for JupyterHub.

Returns
-------
str
    The URL for this provider.

<a id="servir._provide.Provider.create"></a>

##### create

```python
def create(x: pathlib.Path | str | TilesetType,
           **kwargs: typing.Any) -> Resource | TilesetResource[TilesetType]
```

Create a resource from a path or tileset.

Parameters
----------
x : pathlib.Path | str | TilesetProtocol
    The path or tileset to create a resource from.
**kwargs
    Additional keyword arguments to pass to the resource constructor.

Returns
-------
Resource | TilesetResource
    The resource.

<a id="servir._protocols"></a>

### servir.\_protocols

<a id="servir._protocols.ProviderProtocol"></a>

#### ProviderProtocol

```python
class ProviderProtocol(typing.Protocol)
```

A protocol for a provider that can serve resources.

<a id="servir._protocols.ProviderProtocol.url"></a>

##### url

```python
@property
def url() -> str
```

The URL for this provider.

<a id="servir._protocols.TilesetProtocol"></a>

#### TilesetProtocol

```python
class TilesetProtocol(typing.Protocol)
```

Represents a HiGlass Tileset.

<a id="servir._protocols.TilesetProtocol.uid"></a>

##### uid

```python
@property
def uid() -> str
```

The unique identifier for this tileset.

<a id="servir._protocols.TilesetProtocol.tiles"></a>

##### tiles

```python
def tiles(tile_ids: typing.Sequence[str]) -> list[typing.Any]
```

Get the tiles for the given tile IDs.

Parameters
----------
tile_ids : list[str]
    The tile IDs to get.

Returns
-------
list[typing.Any]
    The tiles.

<a id="servir._protocols.TilesetProtocol.info"></a>

##### info

```python
def info() -> dict[str, typing.Any]
```

Get the tileset info for this tileset.

Returns
-------
dict[str, typing.Any]
    The tileset info.

<a id="servir._tilesets"></a>

### servir.\_tilesets

<a id="servir._tilesets.TilesetResource"></a>

#### TilesetResource

```python
class TilesetResource(typing.Generic[TilesetType])
```

A tileset resource.

<a id="servir._tilesets.TilesetResource.__init__"></a>

##### \_\_init\_\_

```python
def __init__(tileset: TilesetType, provider: ProviderProtocol)
```

Initialize a tileset resource.

Parameters
----------
tileset : TilesetProtocol
    The tileset.
provider : ProviderProtocol
    The server provider.

<a id="servir._tilesets.TilesetResource.tileset"></a>

##### tileset

```python
@property
def tileset() -> TilesetType
```

The tileset.

<a id="servir._tilesets.TilesetResource.uid"></a>

##### uid

```python
@property
def uid() -> str
```

The unique identifier for the tileset.

<a id="servir._tilesets.TilesetResource.server"></a>

##### server

```python
@property
def server() -> str
```

The server url.

<a id="servir._tilesets.get_list"></a>

###### get\_list

```python
def get_list(query: str, field: str) -> list[str]
```

Parse chained query params into list.

Parameters
----------
query : str
    The query string. For example, "d=id1&d=id2&d=id3".
field : str
    The field to extract. For example, "d".

Returns
-------
list[str]
    The list of values for the given field. For example, ['id1', 'id2', 'id3'].

<a id="servir._tilesets.tileset_info"></a>

###### tileset\_info

```python
def tileset_info(
    request: Request,
    tilesets: typing.Mapping[str, TilesetResource[TilesetProtocol]]
) -> JSONResponse
```

Request handler for the tileset_info/ endpoint.

Parameters
----------
request : Request
    The request.
tilesets : typing.Mapping[str, TilesetResource]
    The tileset resources.

Returns
-------
JSONResponse
    The server response.

<a id="servir._tilesets.tiles"></a>

###### tiles

```python
def tiles(
    request: Request,
    tilesets: typing.Mapping[str, TilesetResource[TilesetProtocol]]
) -> JSONResponse
```

Request handler for the tiles/ endpoint.

Parameters
----------
request : Request
    The request.
tilesets : typing.Mapping[str, TilesetResource]
    The tileset resources.

Returns
-------
JSONResponse
    The server response.

<a id="servir._tilesets.chromsizes"></a>

###### chromsizes

```python
def chromsizes(
    request: Request,
    tilesets: typing.Mapping[str, TilesetResource[TilesetProtocol]]
) -> PlainTextResponse | JSONResponse
```

Request handler for the chrom-sizes/ endpoint.

Chromsizes are returned as a plain text response, as a TSV:

    chr1    249250621
    chr2    243199373
    ...

Parameters
----------
request : Request
    The request.
tilesets : typing.Mapping[str, TilesetResource]
    The tileset resources.

Returns
-------
PlainTextResponse | JSONResponse
    The server response. If the tileset does not have chromsizes, a JSON
    response with an error message is returned.

<a id="servir._tilesets.create_tileset_route"></a>

###### create\_tileset\_route

```python
def create_tileset_route(tileset_resources: typing.Mapping[
    str, TilesetResource[TilesetProtocol]],
                         scope_id: str = "tilesets") -> Mount
```

Create a route for tileset endpoints.

Parameters
----------
tileset_resources : typing.Mapping[str, TilesetResource]
    The tileset resources.
scope_id : str, optional
    The scope id to use for passing the tileset resources to the
    request handlers, by default "tilesets".

Returns
-------
Mount
    The API route.

<a id="servir._util"></a>

### servir.\_util

<a id="servir._util.md5"></a>

###### md5

```python
def md5(data: str | bytes) -> str
```

Generate a unique identifier for a string or bytes.

Parameters
----------
string : str
    The string to hash.

Returns
-------
str :
    A unique identifier for the string.

<a id="servir._util.create_resource_identifier"></a>

###### create\_resource\_identifier

```python
def create_resource_identifier(data: str | bytes, id: str) -> str
```

Create a unique identifier for a string or bytes.

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

<a id="servir._util.read_file_blocks"></a>

###### read\_file\_blocks

```python
def read_file_blocks(path: pathlib.Path,
                     start: int = 0,
                     end: None | int = None,
                     block_size: int = 65535) -> typing.Iterator[bytes]
```

Read content range as generator from file object.

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

<a id="servir._util.ContentRange"></a>

#### ContentRange

```python
@dataclasses.dataclass(frozen=True)
class ContentRange()
```

<a id="servir._util.ContentRange.parse_header"></a>

##### parse\_header

```python
@classmethod
def parse_header(cls, header: str) -> ContentRange
```

Parse 'Range' header into integer interval.

Does not support multiple ranges.

Parameters
----------
content_range : str
    The 'Range' header.

Returns
-------
tuple[int, int]
    The start and end of the byte-range.

<a id="servir._util.guess_media_type"></a>

###### guess\_media\_type

```python
def guess_media_type(path: str | pathlib.Path) -> str
```

Guess the media type of a file.

Parameters
----------
path : pathlib.Path
    The path to the file.

Returns
-------
str
    The media type.

<a id="servir._background_server"></a>

### servir.\_background\_server

<a id="servir._background_server.BackgroundServer"></a>

#### BackgroundServer

```python
class BackgroundServer()
```

A threading-based background server for Starlette apps.

<a id="servir._background_server.BackgroundServer.__init__"></a>

##### \_\_init\_\_

```python
def __init__(app: ASGIApp) -> None
```

Initialize a background server for the given Starlette app.

Parameters
----------
app : ASGIApp
    The Starlette app to run in the background.

<a id="servir._background_server.BackgroundServer.app"></a>

##### app

```python
@property
def app() -> ASGIApp
```

The Starlette app being run in the background.

<a id="servir._background_server.BackgroundServer.port"></a>

##### port

```python
@property
def port() -> int
```

The port on which the server is running.

<a id="servir._background_server.BackgroundServer.stop"></a>

##### stop

```python
def stop() -> Self
```

Stop the background server thread.

<a id="servir._background_server.BackgroundServer.start"></a>

##### start

```python
def start(port: int | None = None,
          timeout: int = 1,
          daemon: bool = True,
          log_level: str = "warning") -> Self
```

Start app in a background thread.

Parameters
----------
port : int, optional
    The port on which to run the server. If not provided, a random port will be
    selected.
timeout : int, optional
    The timeout for keep-alive connections, by default 1.
daemon : bool, optional
    Whether to run the server thread as a daemon thread, by default True.
log_level : str, optional
    The log level for the server, by default "warning".

Returns
-------
BackgroundServer
    The background server instance.

<a id="servir._resources"></a>

### servir.\_resources

<a id="servir._resources.Resource"></a>

#### Resource

```python
class Resource(metaclass=abc.ABCMeta)
```

A resource that can be served by a provider.

<a id="servir._resources.Resource.__init__"></a>

##### \_\_init\_\_

```python
def __init__(provider: ProviderProtocol,
             headers: None | dict[str, str] = None)
```

Create a new Resource.

Parameters
----------
provider : ProviderProtocol
    The provider that will serve this resource.
headers : dict[str, str], optional
    Additional headers to include in the response.

<a id="servir._resources.Resource.guid"></a>

##### guid

```python
@property
def guid() -> str
```

The unique identifier for this resource.

<a id="servir._resources.Resource.url"></a>

##### url

```python
@property
def url() -> str
```

The URL for this resource.

<a id="servir._resources.Resource.get"></a>

##### get

```python
@abc.abstractmethod
def get(request: Request) -> Response
```

Get the resource.

Parameters
----------
request : Request
    The request to handle.

Returns
-------
Response
    The response to send.

<a id="servir._resources.DirectoryResource"></a>

#### DirectoryResource

```python
class DirectoryResource(Resource)
```

Serve a directory as a resource.

<a id="servir._resources.DirectoryResource.__init__"></a>

##### \_\_init\_\_

```python
def __init__(path: pathlib.Path, **kwargs: typing.Any)
```

Create a new DirectoryResource.

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

<a id="servir._resources.ContentResource"></a>

#### ContentResource

```python
class ContentResource(Resource)
```

Serve a string or bytes as a resource.

<a id="servir._resources.ContentResource.__init__"></a>

##### \_\_init\_\_

```python
def __init__(content: str | bytes,
             extension: None | str = None,
             **kwargs: typing.Any)
```

Create a new ContentResource.

Parameters
----------
content : str | bytes
    The content to serve.
extension : str, optional
    The extension to use for the resource identifier.
kwargs : dict
    Additional keyword arguments to pass to the Resource constructor.

<a id="servir._resources.create_resource_route"></a>

###### create\_resource\_route

```python
def create_resource_route(resources: typing.Mapping[str, Resource]) -> Mount
```

Create a route for serving resources.

Parameters
----------
resources : typing.Mapping[str, Resource]
    A mapping of resource identifiers to resources.

Returns
-------
Mount
    A route for serving resources.

<a id="servir._resources.create_resource"></a>

###### create\_resource

```python
def create_resource(x: pathlib.Path | str, provider: ProviderProtocol,
                    **kwargs: typing.Any) -> Resource
```

Create a resource from a path or string.

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

