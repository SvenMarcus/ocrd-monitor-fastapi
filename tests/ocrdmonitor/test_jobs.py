from dataclasses import replace
from pathlib import Path

from ocrdmonitor.ocrdjob import OcrdJob, KitodoProcessDetails

JOB_DIR = Path("tests/ocrdmonitor/ocrd.jobs")
JOB_TEMPLATE = OcrdJob(
    kitodo_details=KitodoProcessDetails(
        process_id=5432,
        task_id=45989,
        processdir="/data/5432",
    ),
    workdir="ocr-d/data/5432",
    remotedir="/remote/job/dir",
    workflow_file="ocr-workflow-default.sh",
    controller_address="controller.ocrdhost.com",
)


def test__parsing_a_ocrd_job_file_for_completed_job__returns_ocrdjob_with_a_return_code() -> None:
    job_file = JOB_DIR / "completed_job.env"
    content = job_file.read_text()
    actual = OcrdJob.from_str(content)

    expected = replace(JOB_TEMPLATE, return_code=0)
    assert actual == expected


def test__parsing_a_ocrd_job_file_for_running_job__returns_ocrdjob_with_a_process_id() -> None:
    job_file = JOB_DIR / "running_job.env"
    content = job_file.read_text()
    actual = OcrdJob.from_str(content)

    expected = replace(JOB_TEMPLATE, pid=1)
    assert actual == expected
