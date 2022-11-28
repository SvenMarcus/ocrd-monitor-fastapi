from dataclasses import replace
from pathlib import Path
from typing import Generator
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient
from ocrdmonitor.ocrdjob import KitodoProcessDetails, OcrdJob
from ocrdmonitor.processstatus import ProcessStatus

from ocrdmonitor.server.app import PKG_DIR, STATIC_DIR, TEMPLATE_DIR
from ocrdmonitor.server.jobs import ProcessQuery, create_jobs
from ocrdmonitor.server.settings import (
    OcrdBrowserSettings,
    OcrdControllerSettings,
    Settings,
)
from tests.ocrdmonitor.test_jobs import JOB_TEMPLATE, jobfile_content_for

templates = Jinja2Templates(TEMPLATE_DIR)
job_dir = Path(__file__).parent / "ocrd.jobs"


@pytest.fixture(autouse=True)
def create_jobdir() -> Generator[None, None, None]:
    job_dir.mkdir(exist_ok=True)

    yield


def create_settings() -> Settings:
    return Settings(
        browser=OcrdBrowserSettings(
            workspace_dir=Path(),
            port_range=(9000, 9100),
        ),
        controller=OcrdControllerSettings(
            job_dir=job_dir,
            host="",
            user="",
        ),
    )


@pytest.mark.skip()
def test__given_a_completed_ocrd_job__the_job_endpoint_lists_it_in_a_table() -> None:
    completed_job = replace(JOB_TEMPLATE, return_code=0)
    content = jobfile_content_for(completed_job)
    jobfile = job_dir / "jobfile"
    jobfile.touch(exist_ok=True)
    jobfile.write_text(content)

    def dummy_process_query(process_group: int) -> list[ProcessStatus]:
        return []

    patch.object(create_settings(), "process_query", lambda: dummy_process_query)

    sut = make_test_app(dummy_process_query, job_dir)

    result = sut.get("/jobs")
    result.content


def make_test_app(process_query: ProcessQuery, job_dir: Path) -> TestClient:
    app = FastAPI()
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
    app.include_router(create_jobs(templates, process_query, job_dir))
    sut = TestClient(app)
    return sut
