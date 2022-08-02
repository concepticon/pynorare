import logging
import pathlib

import pytest

from pynorare import NormDataSet, NoRaRe


@pytest.fixture
def dataset2(concepticon_api, repos):
    api = NoRaRe(repos)
    return NormDataSet.from_datasetmeta(
        api.datasets['ds2'],
        concepticon=concepticon_api,
        mappings={'fr': {'hut': [('1', 3, 'THING')]}})


def test_NormDataSet(mocker, dataset, caplog):
    mocker.patch(
        'pynorare.dataset.urlretrieve',
        lambda u, f: pathlib.Path(f).write_text(
            'gloss,float,int,POS\nthe gloss,1.2,3,noun\nother gloss,1.2,3', encoding='utf8'))
    with caplog.at_level(logging.INFO):
        dataset.download()
        dataset.map()
        dataset.validate()
        assert dataset.raw_dir.joinpath('data.csv').exists()
        assert 'concepticon' in caplog.records[-1].message
        # Only the first gloss (by line number) matching a specific concept is extracted:
        assert len(list(dataset.meta.table)) == 1
        assert list(dataset.meta.table)[0]['FRENCH'] == 'the gloss'


def test_NormDataSet2(mocker, dataset2, caplog):
    mocker.patch(
        'pynorare.files.urlretrieve',
        # do nothing! file is already there!
        lambda u, f: None)
    with caplog.at_level(logging.INFO):
        dataset2.download()
        dataset2.map()
        dataset2.validate()
        assert 'concepticon' in caplog.records[-1].message
        assert dataset2.mapped
