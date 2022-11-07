from dataclasses import dataclass
import enum


_PS = 'ps -g "%s" --forest -o pid,stat,pcpu,rss,cputime --no-headers'


class ProcessState(enum.Enum):
    RUNNING = "R"
    SLEEPING = "S"
    ZOMBIE = "Z"
    DEAD = "X"


@dataclass
class JobResources:
    id: int
    state: ProcessState
    cpu_utilization: float
    memory: int


def parse_resource_consumption(ps_output: str) -> JobResources:
    pass
