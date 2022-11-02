from pathlib import Path
from typing import Callable
import uuid
from fastapi import Cookie, FastAPI, Request, Response, WebSocket
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
import requests

from ocrdbrowser import workspace, OcrdBrowserFactory, OcrdBrowser
import ocrdbrowser
from ocrdmonitor.redirect import RedirectMap


PKG_DIR = Path(__file__).parent
STATIC_DIR = PKG_DIR / "static"
TEMPLATE_DIR = PKG_DIR / "templates"

WORKSPACE_DIR = Path("ocrd_examples")
BROWSER_FACTORY = ocrdbrowser.DockerOcrdBrowserFactory(
    "http://localhost", set(range(8000, 8001))
)


def _proxy(path: str) -> Response:
    t_resp = requests.request(method="GET", url=path, allow_redirects=False)

    response = Response(
        content=t_resp.content,
        status_code=t_resp.status_code,
        headers=t_resp.headers,
    )

    return response


def create_app(workspace_dir: Path, browser_factory: OcrdBrowserFactory) -> FastAPI:
    app = FastAPI()
    templates = Jinja2Templates(TEMPLATE_DIR)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    running_browsers: set[OcrdBrowser] = set()
    redirects = RedirectMap()

    @app.middleware("http")
    def register_session_id(
        request: Request, call_next: Callable[[Request], Response]
    ) -> Response:
        request.cookies.setdefault("session_id", str(uuid.uuid4()))
        response = call_next(request)
        response.set_cookie(request.cookies["session_id"])
        return response

    @app.get("/")
    def list_workspaces(request: Request) -> Response:
        return templates.TemplateResponse(
            "index.html.j2",
            {"request": request, "workspaces": workspace.list_all(workspace_dir)},
        )

    @app.get("/browse/{workspace:path}")
    def launch_browser(
        request: Request, workspace: str, session_id: str = Cookie(default=None)
    ) -> Response:
        workspace_path = workspace_dir / workspace
        browser = _launch_browser(session_id, workspace_path)
        redirects.add(session_id, workspace_path, browser)

        return templates.TemplateResponse(
            "browser.html.j2",
            {
                "request": request,
                "workspace_id": workspace,
                "browser_url": browser.address(),
            },
        )

    @app.get("/workspace/{workspace:path}")
    def reverse_proxy(
        request: Request, workspace: str, session_id: str = Cookie(default=None)
    ) -> Response:
        workspace_path = workspace_dir / workspace
        redirect = redirects.get(session_id, workspace_path)
        return _proxy(redirect.redirect_url(str(workspace_path)))

    @app.websocket("workspace/{workspace:path}/socket")
    def socket(websocket: WebSocket) -> None:
        while True:
            data = websocket.receive_text()
            websocket.send_text(f"Message text was: {data}")

    def _launch_browser(session_id: str, workspace: Path) -> OcrdBrowser:
        browser = ocrdbrowser.launch(
            str(workspace),
            session_id,
            browser_factory,
            running_browsers,
        )

        running_browsers.add(browser)
        return browser

    return app


app = create_app(WORKSPACE_DIR)
