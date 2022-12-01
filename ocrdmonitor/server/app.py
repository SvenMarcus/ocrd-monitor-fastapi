from functools import partial
import logging
from pathlib import Path
from types import TracebackType
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from ocrdmonitor.sshps import process_status
from ocrdmonitor.server.index import create_index
from ocrdmonitor.server.jobs import create_jobs
from ocrdmonitor.server.logs import create_logs
from ocrdmonitor.server.settings import Settings
from ocrdmonitor.server.workflows import create_workflows
from ocrdmonitor.server.workspaces import create_workspaces

PKG_DIR = Path(__file__).parent
STATIC_DIR = PKG_DIR / "static"
TEMPLATE_DIR = PKG_DIR / "templates"


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI()
    templates = Jinja2Templates(TEMPLATE_DIR)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    # NOTE: 
    # For some reason having this middleware causes an assertion error in the tests
    #
    # @app.middleware("http")
    # async def swallow_exceptions(
    #     request: Request, call_next: Callable[[Request], Awaitable[Response]]
    # ) -> Response:
    #     try:
    #         response = await call_next(request)
    #         return response
    #     except Exception as err:
    #         logging.error(err)
    #         return RedirectResponse("/")

    app.include_router(create_index(templates))
    app.include_router(
        create_jobs(
            templates,
            settings.controller.process_query(),
            settings.controller.job_dir,
        )
    )
    app.include_router(
        create_workspaces(
            templates,
            settings.browser.factory(),
            settings.browser.workspace_dir,
        )
    )
    app.include_router(create_logs(templates))
    app.include_router(create_workflows(templates))

    return app
