import pytest
import subprocess
import testinfra

import uchecker

IMAGES = [
    'centos7',
    'debian8',
    'ubuntu20.04',
]


def docker_host():
    for image in IMAGES:
        subprocess.check_call(['docker', 'build', '-t', '-f' , 'Dockerfile.' + image, '.'])
        docker_id = subprocess.check_output(['docker', 'run', '-itd', image]).decode().strip()
        host = testinfra.get_host("docker://" + docker_id)
        yield host
        # subprocess.check_call(['docker', 'rm', '-f', docker_id])


@pytest.mark.parametrize("host", docker_host())
def test_simple(host):
    cmd = host.run("python -c 'import platform; print(platform.linux_distribution())'")
    assert cmd.rc == 0, cmd.stderr
    assert cmd.stdout == 'test'
