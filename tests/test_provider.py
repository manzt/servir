from typing import MutableMapping

import pytest
from starlette.routing import Mount, Route
from starlette.requests import Request

from bg_server._provide import Provider, ResourceHandler

def test_no_handler():
    provider = Provider(handlers=[])
    with pytest.raises(ValueError):
        provider.add_resource("foo")
