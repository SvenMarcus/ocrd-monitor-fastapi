import datetime
from pathlib import Path
import subprocess
import time
from typing import Generator
import pytest
from testcontainers.general import DockerContainer
from ocrdmonitor.processstatus import ProcessState

from ocrdmonitor.sshps import SSHConfig, status

SSHSERVER_DIR = "tests/ocrdbrowser_server/testcontainers/sshserver"

PS = "ps -o pid --no-headers"


def remove_existing_host_key() -> None:
    subprocess.run("ssh-keygen -R [localhost]:2222", shell=True, check=True)


def configure_container() -> DockerContainer:
    pub_key = Path(SSHSERVER_DIR) / "id.rsa.pub"
    return (
        DockerContainer(image="lscr.io/linuxserver/openssh-server:latest")
        .with_bind_ports(2222, 2222)
        .with_env("PUBLIC_KEY", pub_key.read_text())
        .with_env("USER_NAME", "testcontainer")
    )


@pytest.fixture
def openssh_server() -> Generator[DockerContainer, None, None]:
    remove_existing_host_key()
    with configure_container() as container:
        time.sleep(1)  # wait for ssh server to start
        yield container


def get_process_group_from_container(container: DockerContainer) -> int:
    result = container.exec(PS)
    return int(result.output.splitlines()[0].strip())


def test_ps_over_ssh__returns_list_of_process_status(
    openssh_server: DockerContainer,
) -> None:
    process_group = get_process_group_from_container(openssh_server)

    actual = status(
        config=SSHConfig(
            host="localhost",
            port=2222,
            user="testcontainer",
            keyfile=str(Path(SSHSERVER_DIR).absolute() / "id.rsa"),
        ),
        process_group=process_group,
    )

    first_process = actual[0]
    assert first_process.pid == process_group
    assert first_process.state == ProcessState.SLEEPING
