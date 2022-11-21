from dataclasses import dataclass
from datetime import timedelta
from enum import Enum


PS_CMD = "ps -g {} -e pid,state,%cpu,rss,cputime --no-headers"


class ProcessState(Enum):
    RUNNING = "R"
    SLEEPING = "S"
    STOPPED = "T"
    ZOMBIE = "Z"
    UNKNOWN = "?"


@dataclass(frozen=True)
class ProcessStatus:
    pid: int
    state: ProcessState
    percent_cpu: float
    memory: int
    cpu_time: timedelta

    @classmethod
    def from_ps_output(cls, ps_output: str) -> list["ProcessStatus"]:
        lines = ps_output.strip().splitlines()

        def parse_line(line: str) -> "ProcessStatus":
            pid, state, percent_cpu, memory, cpu_time, *_ = line.split()
            return cls(
                pid=int(pid),
                state=ProcessState(state[0]),
                percent_cpu=float(percent_cpu),
                memory=int(memory),
                cpu_time=timedelta(seconds=_cpu_time_to_seconds(cpu_time)),
            )

        return [parse_line(line) for line in lines]


def _cpu_time_to_seconds(cpu_time: str) -> int:
    hours, minutes, seconds = cpu_time.split(":")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds)
