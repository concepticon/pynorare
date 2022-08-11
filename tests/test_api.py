import pytest

from pynorare import NoRaRe


@pytest.fixture
def api(repos, concepticon_api):
    return NoRaRe(repos=repos, concepticon=concepticon_api)


def test_NoRaRe(api):
    assert len(api.refs) == 1
    assert len(api.datasets) == 3
    assert api.datasets['dsid'].concepts


def test_Dataset_download_zip(api, mocker):
    mocker.patch(
        'pynorare.api.urllib.request',
        mocker.Mock(urlretrieve=lambda u, t: 1))
    ds = api.datasets['ds2']
    ds.download_zip('x', 'f.zip', 'norare.xlsx')
    assert len(ds.get_excel('norare.xlsx')) == 2


def test_Dataset_get_excel(api):
    res = api.datasets['ds2'].get_excel('test.xls', 0)
    assert len(res) == 5857
