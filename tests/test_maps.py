import pytest
import mock

import uchecker
from mock import patch, mock_open


@pytest.fixture
def proc(tmpdir):
    tmpdir.join('10').join('maps').write('', ensure=True)

    proc_map = [
        '7f0d604f4000-7f0d604f5000 rw-p 00003000 08:02 1976429                    /usr/lib/libX11-xcb.so.1.0.0',
        '7f0d604f8000-7f0d604fa000 r--p 00000000 08:02 2230515                    /usr/lib/qt/plugins/platforms/libqxcb.so'
    ]
    tmpdir.join('100').join('maps').write('\n'.join(proc_map), ensure=True)
    tmpdir.join('100').join('comm').write('cat', ensure=True)
    with mock.patch('uchecker.PROC_SRC', str(tmpdir)):
        yield


def test_iter_maps(proc):
    # PID does not exists
    assert list(uchecker.iter_maps(-1)) == []

    # Empty
    assert list(uchecker.iter_maps(10)) == []

    # Existing process
    assert list(uchecker.iter_maps(100)) == [
        uchecker.Map(addr='7f0d604f4000-7f0d604f5000', perm='rw-p', offset='00003000', dev='08:02', inode='1976429', pathname='/usr/lib/libX11-xcb.so.1.0.0', flag=None),
        uchecker.Map(addr='7f0d604f8000-7f0d604fa000', perm='r--p', offset='00000000', dev='08:02', inode='2230515', pathname='/usr/lib/qt/plugins/platforms/libqxcb.so', flag=None)
    ]


def test_get_comm(proc):
    assert uchecker.get_comm(100) == 'cat'


def test_iter_pids(proc):
    assert list(uchecker.iter_pids())


def test_iter_proc_map(proc):
    assert list(uchecker.iter_proc_map())


def test_iter_proc_lib(proc):
    assert list(uchecker.iter_proc_lib())
