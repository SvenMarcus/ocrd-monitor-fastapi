from dataclasses import dataclass
from typing import Any, NamedTuple, Type


_KEYMAP: dict[str, tuple[Type[int] | Type[str], str]] = {
    "RETVAL": (int, "return_code"),
    "PROCESS_ID": (int, "process_id"),
    "TASK_ID": (int, "task_id"),
    "PROCESS_DIR": (str, "processdir"),
    "WORKDIR": (str, "workdir"),
    "REMOTEDIR": (str, "remotedir"),
    "WORKFLOW": (str, "workflow_file"),
    "CONTROLLER": (str, "controller_address"),
}


def _into_dict(content: str) -> dict[str, int | str]:
    result_dict = {}
    lines = content.splitlines()
    for line in lines:
        key, value = line.split("=")
        if key not in _KEYMAP:
            continue

        value_type, keyname = _KEYMAP[key]
        result_dict[keyname] = value_type(value)

    return result_dict


class KitodoProcessDetails(NamedTuple):
    process_id: int
    task_id: int
    processdir: str


def _pop_kitodo_details(d: dict[str, Any]) -> dict[str, Any]:
    return {
        "process_id": d.pop("process_id"),
        "task_id": d.pop("task_id"),
        "processdir": d.pop("processdir"),
    }


@dataclass(frozen=True)
class OcrdJob:
    kitodo_details: KitodoProcessDetails
    workdir: str
    remotedir: str
    workflow_file: str
    controller_address: str

    process_id: int | None = None
    return_code: int | None = None

    @classmethod
    def from_str(cls, content: str) -> "OcrdJob":
        """
        Parse a job file consisting of key=value pairs.
        """
        parsed_dict = _into_dict(content)
        kitodo_dict = _pop_kitodo_details(parsed_dict)
        parsed_dict["kitodo_details"] = KitodoProcessDetails(**kitodo_dict)  # type: ignore
        return cls(**parsed_dict)  # type: ignore
