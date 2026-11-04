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
        'pynorare.api.download_file', lambda _url, path: path)
    ds = api.datasets['ds2']
    ds.download_zip('x', 'f.zip', 'norare.xlsx')
    assert len(ds.get_excel('norare.xlsx')) == 2


def test_Dataset_get_excel(api):
    res = api.datasets['ds2'].get_excel('test.xls', 0)
    assert len(res) == 5857


@pytest.mark.parametrize('pos,mapper,candidates,expected', [
    ('noun', {'noun': 'Person/Thing'}, [('1', 2, 'Property')], None),
    ('noun', {'noun': 'Person/Thing'}, [('2', 2, 'Person/Thing')], '2'),
    ('Person/Thing', {}, [('2', 2, 'Person/Thing')], '2'),
    ('noun', {'noun': 'Person/Thing'}, [('2', 3, 'Person/Thing'), ('4', 2, 'Person/Thing')], '2'),
    ('noun', {'noun': 'Person/Thing'}, [('1', 3, 'Property'), ('2', 2, 'Person/Thing')], '2'),
])
def test_Dataset_extract_data_pos(api, concepticon_api, mocker, pos, mapper, candidates, expected):
    ds = api.datasets['dsid']
    write = mocker.patch.object(ds, 'write_table')
    ds.extract_data(
        [{'FRENCH': 'the gloss', 'POS': pos}], concepticon_api,
        {'fr': {'the gloss': candidates}}, gloss='FRENCH', language='fr',
        pos=True, pos_mapper=mapper)
    written = write.call_args[0][0]
    assert [row['CONCEPTICON_ID'] for row in written] == ([expected] if expected else [])
