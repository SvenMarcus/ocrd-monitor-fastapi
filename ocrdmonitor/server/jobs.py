from dataclasses import dataclass
import itertools
from pathlib import Path
from typing import Protocol

from fastapi import APIRouter, Request, Response
from fastapi.templating import Jinja2Templates

from ocrdmonitor.ocrdjob import OcrdJob
from ocrdmonitor.processstatus import ProcessStatus


@dataclass
class RunningJob:
    ocrd_job: OcrdJob
    process_status: ProcessStatus


class ProcessQuery(Protocol):
    def __call__(self, process_group: int) -> list[ProcessStatus]:
        ...


class OcrdController:
    def __init__(self, process_query: ProcessQuery, job_dir: Path) -> None:
        self._process_query = process_query
        self._job_dir = job_dir

    def get_jobs(self) -> list[OcrdJob]:
        return [
            OcrdJob.from_str(job_file.read_text())
            for job_file in self._job_dir.iterdir()
        ]

    def status_for(self, ocrd_job: OcrdJob) -> ProcessStatus | None:
        if ocrd_job.pid is None:
            return None

        process_statuses = self._process_query(ocrd_job.pid)
        return next(
            (status for status in process_statuses if status.pid == ocrd_job.pid), None
        )


def create_jobs(
    templates: Jinja2Templates, process_query: ProcessQuery, job_dir: Path
) -> APIRouter:
    controller = OcrdController(process_query, job_dir)

    router = APIRouter(prefix="/jobs")

    @router.get("/", name="jobs")
    def jobs(request: Request) -> Response:
        jobs = controller.get_jobs()

        running_ocrd_jobs = [job for job in jobs if job.is_running]
        completed_ocrd_jobs = [job for job in jobs if job.is_completed]

        # nested_job_status = [
        #     process_query(job.pid) for job in running_ocrd_jobs if job.pid is not None
        # ]

        # flattened_job_status = list(itertools.chain.from_iterable(nested_job_status))

        flattened_job_status = [controller.status_for(job) for job in running_ocrd_jobs]
        running_jobs = [
            RunningJob(job, process_status)
            for job, process_status in zip(running_ocrd_jobs, flattened_job_status)
            if process_status is not None
        ]

        return templates.TemplateResponse(
            "jobs.html.j2",
            {
                "request": request,
                "running_jobs": running_jobs,
                "completed_jobs": completed_ocrd_jobs,
            },
        )

    return router
