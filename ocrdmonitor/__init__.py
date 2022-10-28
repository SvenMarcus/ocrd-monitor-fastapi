from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

PKG_DIR = Path(__file__).parent
STATIC_DIR = PKG_DIR / "static"
TEMPLATE_DIR = PKG_DIR / "templates"


def create_app() -> FastAPI:
    app = FastAPI()
    templates = Jinja2Templates(TEMPLATE_DIR)
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    return app
