from pathlib import Path
from typing import Protocol


class WorkspaceServer(Protocol):
    def address(self) -> str:
        ...


class WorkspaceRedirect:
    def __init__(self, workspace: Path, server: WorkspaceServer) -> None:
        self._workspace = workspace
        self._server = server

    def redirect_url(self, url: str) -> str:
        url = url.removeprefix(str(self._workspace)).removeprefix("/")
        address = self._server.address().removesuffix("/")
        return (address + "/" + url).removesuffix("/")
