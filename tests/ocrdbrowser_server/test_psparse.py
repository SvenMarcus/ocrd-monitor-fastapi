import datetime
from ocrdmonitor.processstatus import ProcessState, ProcessStatus


def test__parsing_psoutput__returns_list_of_process_status() -> None:
    out = ProcessStatus.from_ps_output(
        """
        1  Ss   0.0  3872 01:12:46
        20 R+  49.7  1556 02:33:02
        """
    )

    assert out == [
        ProcessStatus(
            pid=1,
            state=ProcessState.SLEEPING,
            percent_cpu=0.0,
            memory=3872,
            cpu_time=datetime.timedelta(hours=1, minutes=12, seconds=46),
        ),
        ProcessStatus(
            pid=20,
            state=ProcessState.RUNNING,
            percent_cpu=49.7,
            memory=1556,
            cpu_time=datetime.timedelta(hours=2, minutes=33, seconds=2),
        ),
    ]


def test__parsing_psoutput__returns_empty_list_for_empty_output() -> None:
    out = ProcessStatus.from_ps_output("")

    assert out == []
