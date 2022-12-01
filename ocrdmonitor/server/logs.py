from pathlib import Path
from fastapi import APIRouter, Request, Response
from fastapi.templating import Jinja2Templates


def create_logs(templates: Jinja2Templates) -> APIRouter:
    router = APIRouter(prefix="/logs")

    @router.get("/view/{path:path}", name="logs.view")
    def logs(request: Request, path: Path) -> Response:
        if not path.exists():
            return Response(status_code=404)

        if not path.as_posix().endswith("ocrd.log"):
            path = path / "ocrd.log"

        content = path.read_text()

        return templates.TemplateResponse(
            "logs.html.j2", {"request": request, "logs": content}
        )

    return router
