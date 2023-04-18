# bgserve

an extensible async background server for python

[![PyPI - Version](https://img.shields.io/pypi/v/bgserve.svg)](https://pypi.org/project/bgserve)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bgserve.svg)](https://pypi.org/project/bgserve)

-----

**table of contents**

- [installation](#installation)
- [usage](#usage)
- [license](#license)

## installation

```console
pip install bgserve
```

## usage

```python
import pathlib

import requests
from bgserve import Provider

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

`bgserve` is distributed under the terms of the [MIT](https://spdx.org/licenses/MIT.html) license.
