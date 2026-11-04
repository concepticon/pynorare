import pytest

from pynorare import NoRaRe


@pytest.fixture
def api(repos, concepticon_api):
    return NoRaRe(repos=repos, concepticon=concepticon_api)


@pytest.mark.parametrize('rows', [[], [{
    'CONCEPTICON_ID': 2, 'CONCEPTICON_GLOSS': 'DUST', 'LINE_IN_SOURCE': 1,
}]])
def test_Dataset_validate(api, rows):
    ds = api.datasets['dsid']
    ds.write_table(rows)
    before = (ds.norare_dsdir / 'dsid.tsv').read_bytes()
    ds.validate()
    assert (ds.norare_dsdir / 'dsid.tsv').read_bytes() == before


def test_Dataset_validate_invalid(api):
    ds = api.datasets['dsid']
    (ds.norare_dsdir / 'dsid.tsv').write_text(
        'CONCEPTICON_ID\tCONCEPTICON_GLOSS\tLINE_IN_SOURCE\ninvalid\tDUST\t1\n', encoding='utf8')
    with pytest.raises(ValueError):
        ds.validate()
