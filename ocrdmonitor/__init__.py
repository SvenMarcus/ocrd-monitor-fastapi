import logging
import uuid
from pathlib import Path
from typing import Awaitable, Callable

import ocrdbrowser
from fastapi import Cookie, FastAPI, Request, Response, WebSocket
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ocrdbrowser import OcrdBrowser, workspace
from websockets.typing import Subprotocol

import ocrdmonitor.proxy as proxy
from ocrdmonitor.redirect import RedirectMap

PKG_DIR = Path(__file__).parent
STATIC_DIR = PKG_DIR / "static"
TEMPLATE_DIR = PKG_DIR / "templates"

WORKSPACE_DIR = Path("ocrd_examples")
BROWSER_FACTORY = ocrdbrowser.DockerOcrdBrowserFactory(
    "http://localhost", set(range(9000, 9100))
)


app = FastAPI()
templates = Jinja2Templates(TEMPLATE_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

running_browsers: set[OcrdBrowser] = set()
redirects = RedirectMap()


@app.middleware("http")
async def assert_session_id(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    request.cookies.setdefault("session_id", str(uuid.uuid4()))
    response = await call_next(request)
    response.set_cookie(request.cookies["session_id"])
    return response


@app.middleware("http")
async def swallow_exceptions(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    try:
        response = await call_next(request)
        return response
    except Exception as err:
        logging.error(err)
        return RedirectResponse("/")


@app.get("/")
def list_workspaces(request: Request) -> Response:
    return templates.TemplateResponse(
        "index.html.j2",
        {"request": request, "workspaces": workspace.list_all(WORKSPACE_DIR)},
    )


@app.get("/workspace/{workspace:path}")
def _(
    request: Request, workspace: str, session_id: str = Cookie(default=None)
) -> Response:
    workspace_path = Path(workspace)
    browser = _launch_browser(session_id, workspace_path)
    redirects.add(session_id, workspace_path, browser)

    return templates.TemplateResponse(
        "workspace.html.j2",
        {"request": request, "workspace": workspace},
    )


@app.get("/view/{workspace:path}")
def _(workspace: str, session_id: str = Cookie(default=None)) -> Response:
    workspace_path = Path(workspace)
    redirect = redirects.get(session_id, workspace_path)
    return proxy.forward(redirect, str(workspace_path))


@app.websocket("/view/{workspace:path}/socket")
async def _(
    websocket: WebSocket, workspace: Path, session_id: str = Cookie(default=None)
) -> None:
    redirect = redirects.get(session_id, workspace)
    url = redirect.redirect_url(str(workspace / "socket"))
    await websocket.accept(subprotocol="broadway")

    async with proxy.WebSocketAdapter(
        url, [Subprotocol("broadway")]
    ) as broadway_socket:
        while True:
            await proxy.tunnel(broadway_socket, websocket)


def _launch_browser(session_id: str, workspace: Path) -> OcrdBrowser:
    browser = ocrdbrowser.launch(
        str(workspace).strip("/"),
        session_id,
        BROWSER_FACTORY,
        running_browsers,
    )

    running_browsers.add(browser)
    return browser
