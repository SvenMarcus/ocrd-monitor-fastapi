import logging
import uuid
from pathlib import Path
from typing import Awaitable, Callable

from fastapi import FastAPI, Request, Response
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from ocrdmonitor.server.index import create_index
from ocrdmonitor.server.jobs import create_jobs

from ocrdmonitor.server.workspaces import create_workspaces

PKG_DIR = Path(__file__).parent
STATIC_DIR = PKG_DIR / "static"
TEMPLATE_DIR = PKG_DIR / "templates"


app = FastAPI()
templates = Jinja2Templates(TEMPLATE_DIR)
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


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


app.include_router(create_index(templates))
app.include_router(create_jobs(templates))
app.include_router(create_workspaces(templates))
