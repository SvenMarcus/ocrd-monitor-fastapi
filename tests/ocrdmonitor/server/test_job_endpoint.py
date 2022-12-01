from dataclasses import replace
from pathlib import Path
from typing import Generator

import pytest
from bs4 import BeautifulSoup
from fastapi.templating import Jinja2Templates
from fastapi.testclient import TestClient
from ocrdmonitor.ocrdjob import OcrdJob

from ocrdmonitor.server.app import TEMPLATE_DIR, create_app
from ocrdmonitor.server.settings import (
    OcrdBrowserSettings,
    OcrdControllerSettings,
    Settings,
)
from tests.ocrdmonitor.test_jobs import JOB_TEMPLATE, jobfile_content_for

templates = Jinja2Templates(TEMPLATE_DIR)
job_dir = Path(__file__).parent / "ocrd.jobs"


@pytest.fixture(autouse=True)
def prepare_and_clean_files() -> Generator[None, None, None]:
    job_dir.mkdir(exist_ok=True)

    yield

    for jobfile in job_dir.glob("*"):
        jobfile.unlink()

    job_dir.rmdir()


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


def test__given_a_completed_ocrd_job__the_job_endpoint_lists_it_in_a_table() -> None:
    completed_job = replace(JOB_TEMPLATE, return_code=0)
    write_job_file_for(completed_job)
    settings = create_settings()
    sut = TestClient(create_app(settings))

    result = sut.get("/jobs/")

    table_id = "completed-jobs"
    soup = BeautifulSoup(result.content, "html.parser")
    texts = collect_texts_from_job_table(soup, table_id)

    assert result.is_success
    assert texts == [
        str(completed_job.kitodo_details.task_id),
        str(completed_job.kitodo_details.process_id),
        completed_job.workflow_file.name,
        f"{completed_job.return_code} (SUCCESS)",
        completed_job.kitodo_details.processdir.name,
        "ocrd.log",
    ]


def collect_texts_from_job_table(soup: BeautifulSoup, table_id: str) -> list[str]:
    cells_with_text = soup.select(f"#{table_id} td:not(:has(a)), #{table_id} td > a")
    texts = [r.text for r in cells_with_text]
    return texts


def write_job_file_for(completed_job: OcrdJob) -> None:
    content = jobfile_content_for(completed_job)
    jobfile = job_dir / "jobfile"
    jobfile.touch(exist_ok=True)
    jobfile.write_text(content)
