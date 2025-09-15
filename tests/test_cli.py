import pytest
import sys
from download_swot import download_swot

def test_invalid_protocol(monkeypatch):
    test_args = ['prog', '--protocol', 'sftp']
    monkeypatch.setattr(sys, 'argv', test_args)
    with pytest.raises(SystemExit) as excinfo:
        download_swot.main()
    assert excinfo.value.code == 2
