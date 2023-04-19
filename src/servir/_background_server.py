from __future__ import annotations

import sys
import threading
import time

import portpicker
import uvicorn
from starlette.types import ASGIApp

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self


class BackgroundServer:
    """A threading-based background server for Starlette apps."""

    _app: ASGIApp
    _port: int | None
    _server_thread: threading.Thread | None
    _server: uvicorn.Server | None

    def __init__(self, app: ASGIApp) -> None:
        """Initialize a background server for the given Starlette app.

        Parameters
        ----------
        app : ASGIApp
            The Starlette app to run in the background.
        """
        self._app = app
        self._port = None
        self._server_thread = None
        self._server = None

    @property
    def app(self) -> ASGIApp:
        """The Starlette app being run in the background."""
        return self._app

    @property
    def port(self) -> int:
        """The port on which the server is running."""
        if self._server_thread is None or self._port is None:
            raise RuntimeError("Server not running.")
        return self._port

    def stop(self) -> Self:
        """Stop the background server thread."""
        if self._server_thread is None:
            return self
        assert self._server is not None

        try:
            # queue exit event and wait for thread to terminate
            self._server.should_exit = True
            self._server_thread.join()
        finally:
            self._server = None
            self._server_thread = None

        return self

    def start(
        self,
        port: int | None = None,
        timeout: int = 1,
        daemon: bool = True,
        log_level: str = "warning",
    ) -> Self:
        """Start app in a background thread.

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
        """
        if self._server_thread is not None:
            return self

        config = uvicorn.Config(
            app=self.app,
            port=port or portpicker.pick_unused_port(),
            timeout_keep_alive=timeout,
            log_level=log_level,
        )

        self._port = config.port
        self._server = uvicorn.Server(config=config)
        self._server_thread = threading.Thread(target=self._server.run, daemon=daemon)
        self._server_thread.start()

        # wait for the server to start
        while not self._server.started:
            time.sleep(1e-3)

        return self
