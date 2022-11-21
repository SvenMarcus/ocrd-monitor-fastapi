from pathlib import Path

from ocrdmonitor.jobs import OcrdJob, KitodoProcessDetails


def test__parsing_a_ocrd_job_file__returns_ocrdjob() -> None:
    job_path = Path("tests/ocrdbrowser_server/ocrd.jobs/completed_job.env")
    with job_path.open("r") as f:
        content = f.read()
        actual = OcrdJob.from_str(content)

    assert actual == OcrdJob(
        return_code=0,
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
