from dataclasses import dataclass
from datetime import timedelta
import itertools

from pathlib import Path
from fastapi import APIRouter, Request, Response
from fastapi.templating import Jinja2Templates

from ocrdmonitor.ocrdjob import OcrdJob
from ocrdmonitor.processstatus import ProcessState, ProcessStatus
from ocrdmonitor.sshps import status, SSHConfig


JOB_FOLDER = Path("tests/ocrdbrowser_server/ocrd.jobs")

ssh_config = SSHConfig(
    host="controller.ocrdhost.com",
    user="ocrd",
    port=22,
    keyfile="tests/ocrdbrowser_server/ssh/id_rsa",
)


@dataclass
class RunningJob:
    ocrd_job: OcrdJob
    process_status: ProcessStatus


DUMMY_PROCESS_STATES = [
    ProcessStatus(
        pid=1,
        state=ProcessState.SLEEPING,
        percent_cpu=0.0,
        memory=0,
        cpu_time=timedelta(seconds=0),
    ),
    ProcessStatus(
        pid=2,
        state=ProcessState.RUNNING,
        percent_cpu=0.0,
        memory=0,
        cpu_time=timedelta(seconds=0),
    ),
]


def create_jobs(templates: Jinja2Templates) -> APIRouter:
    router = APIRouter(prefix="/jobs")

    @router.get("/jobs", name="jobs")
    def jobs(request: Request) -> Response:
        job_files = JOB_FOLDER.glob("*")
        jobs = [OcrdJob.from_str(job_file.read_text()) for job_file in job_files]

        running_ocrd_jobs = [job for job in jobs if job.pid is not None]
        completed_jobs = [job for job in jobs if job.return_code is not None]

        # nested_job_status = [
        #     status(ssh_config, job.pid)
        #     for job in running_ocrd_jobs
        #     if job.pid is not None
        # ]

        # flattened_job_status = list(itertools.chain.from_iterable(nested_job_status))
        flattened_job_status = DUMMY_PROCESS_STATES
        running_jobs = [
            RunningJob(job, process_status)
            for job, process_status in zip(running_ocrd_jobs, flattened_job_status)
        ]

        return templates.TemplateResponse(
            "jobs.html.j2",
            {
                "request": request,
                "running_jobs": running_jobs,
                "completed_jobs": completed_jobs,
            },
        )

    return router
