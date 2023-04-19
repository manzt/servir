# servir

[![PyPI - Version](https://img.shields.io/pypi/v/servir.svg)](https://pypi.org/project/servir)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/servir.svg)](https://pypi.org/project/servir)

an extensible async background server for python

-----

**table of contents**

- [installation](#installation)
- [usage](#usage)
- [license](#license)

## installation

```console
pip install servir
```

## usage

```python
import pathlib

import requests
from servir import Provider

# create a provider
provider = Provider()


### File (supports range requests)

path = pathlib.Path("hello.txt")
path.write_text("hello, world")

file_resource = provider.create(path)
response = requests.get(file_resource.url)
assert response.text == "hello, world"
assert "text/plain" in response.headers["Content-Type"] 

### Directory (supports range requests)

root = pathlib.Path("data_dir")
root.mkdir()
(root / "hello.txt").write_text("hello, world")

dir_resource = provider.create(root)
response = requests.get(file_resource.url + "/hello.txt")
assert response.text == "hello, world"
assert "text/plain" in response.headers["Content-Type"]


### In-memory

data = "a,b,c,\n1,2,3,\n4,5,6"

content_resource = provider.create(data, extension=".csv")
response = requests.get(content_resource.url)
assert response.text == data
assert "text/csv" in response.headers["Content-Type"]
```

## license

`servir` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
