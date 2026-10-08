import pytest
from download_swot.listing import list_ftp_files
from download_swot.utils.normalize import normalize_pass_ids

# Test normalization of pass_ids (public utility)
def test_normalize_pass_ids():
    user_pass_ids = ['2', '02', '002', '123']
    expected = {'002', '123'}
    assert normalize_pass_ids(user_pass_ids) == expected

# Test filtering logic in list_ftp_files (mocked)
def test_list_ftp_files_filters_by_pass_id(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_001_002_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_001_123_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_001_999_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.listing.ftplib.FTP', FakeFTP)
    result = list_ftp_files(
        version='v2_0_1',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids={'002', '123'}
    )
    assert len(result) == 2
    assert all(any(pid in r[2] for pid in ['002', '123']) for r in result)

# Test that all files are included if pass_ids is None
def test_list_ftp_files_no_filter(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_001_002_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_001_123_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_001_999_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.listing.ftplib.FTP', FakeFTP)
    result = list_ftp_files(
        version='v2_0_1',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids=None
    )
    assert len(result) == 3

# Test cycle filtering by list
def test_list_ftp_files_cycle_list(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_002_002_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001', 'cycle_002', 'cycle_003']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.listing.ftplib.FTP', FakeFTP)
    result = list_ftp_files(
        version='v2_0_1',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids=None,
        cycle_list=[2]
    )
    assert all('cycle_002' in r[1] for r in result)

# Test cycle filtering by min/max
def test_list_ftp_files_cycle_min_max(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_002_002_20230101T000000_20230101T235959_v2.0.1.nc',
        'SWOT_L3_LR_SSH_Unsmoothed_003_003_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001', 'cycle_002', 'cycle_003']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.listing.ftplib.FTP', FakeFTP)
    result = list_ftp_files(
        version='v2_0_1',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids=None,
        cycle_min=2,
        cycle_max=3
    )
    assert all(any(f'cycle_00{c}' in r[1] for c in [2,3]) for r in result)

# Test precedence: cycle_list over min/max
def test_list_ftp_files_cycle_list_precedence(monkeypatch):
    fake_files = [
        'SWOT_L3_LR_SSH_Unsmoothed_002_002_20230101T000000_20230101T235959_v2.0.1.nc',
    ]
    fake_cycle_folders = ['cycle_001', 'cycle_002', 'cycle_003']
    class FakeFTP:
        def __init__(self, *a, **kw): pass
        def __enter__(self): return self
        def __exit__(self, exc_type, exc_val, exc_tb): pass
        def login(self, *a, **kw): pass
        def cwd(self, *a, **kw): pass
        def nlst(self):
            if not hasattr(self, 'called'):
                self.called = True
                return fake_cycle_folders
            return fake_files
    monkeypatch.setattr('download_swot.listing.ftplib.FTP', FakeFTP)
    result = list_ftp_files(
        version='v2_0_1',
        dtype='Unsmoothed',
        username='user',
        password='pw',
        pass_ids=None,
        cycle_list=[2],
        cycle_min=1,
        cycle_max=3
    )
    assert all('cycle_002' in r[1] for r in result)
    assert len(result) == 1
    assert all(r[2].endswith('.nc') for r in result)


# v3_0 adds a stream level (forward/, reproc/) between dtype and cycle_XXX
def test_list_ftp_files_v3_stream_layout(monkeypatch):
    base = '/swot_products/l3_karin_nadir/l3_lr_ssh/v3_0/Basic'
    tree = {
        base: ['forward', 'reproc'],
        f'{base}/forward': ['cycle_040'],
        f'{base}/reproc': ['cycle_001', 'cycle_474'],
        f'{base}/forward/cycle_040': ['SWOT_L3_LR_SSH_Basic_040_002_20260101T000000_20260101T005959_v3.0.nc'],
        f'{base}/reproc/cycle_001': ['SWOT_L3_LR_SSH_Basic_001_002_20230726T000000_20230726T005959_v3.0.nc'],
        f'{base}/reproc/cycle_474': ['SWOT_L3_LR_SSH_Basic_474_002_20230401T000000_20230401T005959_v3.0.nc'],
    }

    class FakeFTP:
        def __init__(self, *a, **kw): self.path = '/'
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def login(self, *a, **kw): pass
        def cwd(self, path): self.path = path
        def nlst(self): return tree[self.path]

    monkeypatch.setattr('download_swot.listing.ftplib.FTP', FakeFTP)
    result = list_ftp_files(version='v3_0', dtype='Basic', username='u', password='p',
                            cycle_min=1, cycle_max=100)
    assert sorted(r[1] for r in result) == ['cycle_001', 'cycle_040']
    assert {r[0] for r in result} == {
        f'{base}/forward/cycle_040/{tree[f"{base}/forward/cycle_040"][0]}',
        f'{base}/reproc/cycle_001/{tree[f"{base}/reproc/cycle_001"][0]}',
    }
