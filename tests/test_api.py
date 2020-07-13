from pynorare import NoRaRe


def test_NoRaRe(repos, concepticon_api, dataset):
    api = NoRaRe(repos=repos, concepticon=concepticon_api)
    assert len(api.refs) == 1
    assert len(api.datasets) == 2
    assert api.datasets['dsid'].columns
    assert api.datasets['dsid'].concepts
