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


def create_jobs(
    templates: Jinja2Templates, process_query: ProcessQuery, job_dir: Path
) -> APIRouter:

    router = APIRouter(prefix="/jobs")

    @router.get("/jobs", name="jobs")
    def jobs(request: Request) -> Response:
        job_files = job_dir.glob("*")
        jobs = [OcrdJob.from_str(job_file.read_text()) for job_file in job_files]

        running_ocrd_jobs = [job for job in jobs if job.is_running]
        completed_ocrd_jobs = [job for job in jobs if job.is_completed]

        nested_job_status = [
            process_query(job.pid) for job in running_ocrd_jobs if job.pid is not None
        ]

        flattened_job_status = list(itertools.chain.from_iterable(nested_job_status))
        running_jobs = [
            RunningJob(job, process_status)
            for job, process_status in zip(running_ocrd_jobs, flattened_job_status)
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
