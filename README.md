# bg-server

[![PyPI - Version](https://img.shields.io/pypi/v/bg-server.svg)](https://pypi.org/project/bg-server)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bg-server.svg)](https://pypi.org/project/bg-server)

-----

**table of contents**

- [installation](#installation)
- [usage](#usage)
- [license](#license)

## installation

```console
pip install bg-server
```

## usage

```python
import pathlib

import requests
from bg_server import Provider, FileProviderMount, ContentProviderMount

# create a provider
provider = Provider(
    routes=[
        FileProviderMount("/files"),
        ContentProviderMount("/content"),
    ],
)


### File (supports range requests)

path = pathlib.Path("hello.txt")
path.write_text("hello, world")

# create a resource on the server for your file
# starts a background thread the first time a resource is initialized
file_resource = provider.create(path)

response = requests.get(file_resource.url)
assert response.text == "hello, world"
assert "text/plain" in response.headers["Content-Type"] # inferred from file extension


### In-memory

data = "a,b,c,\n1,2,3,\n4,5,6"

content_resource = provider.create(data, extension=".csv")
response = requests.get(content_resource.url)
assert response.text == data
assert "text/csv" in response.headers["Content-Type"]
```

## license

`bg-server` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
