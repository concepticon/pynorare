import logging
import pathlib

import pytest

from pynorare import get_dataset_cls


@pytest.fixture
def dataset(concepticon_api, repos):
    cls = get_dataset_cls(repos / 'concept_set_meta' / 'dsid')
    return cls(
        repos=repos,
        concepticon=concepticon_api,
        mappings={'fr': {'the gloss': [('1', 3, 'THING')]}})


def test_NormDataSet(mocker, dataset, caplog):
    mocker.patch(
        'pynorare.dataset.urlretrieve',
        lambda u, f: pathlib.Path(f).write_text(
            'gloss,float,int\nthe gloss,1.2,3', encoding='utf8'))
    dataset.download()
    assert dataset.raw_dir.joinpath('data.csv').exists()
    dataset.map()
    with caplog.at_level(logging.INFO):
        dataset.validate()
        assert 'concepticon' in caplog.records[-1].message
