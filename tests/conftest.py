import shutil
import pathlib

import pytest
from clldutils import jsonlib
from pyconcepticon.test_util import TEST_REPOS
from pyconcepticon import Concepticon

from pynorare.dataset import get_dataset_cls


@pytest.fixture
def repos(tmpdir):
    shutil.copytree(str(pathlib.Path(__file__).parent / 'repos'), str(tmpdir.join('repos')))
    return pathlib.Path(str(tmpdir)) / 'repos'


@pytest.fixture
def concepticon_api(tmpdir):
    concepticon_repos = pathlib.Path(str(tmpdir.join('concepticon-data')))
    shutil.copytree(str(TEST_REPOS), str(concepticon_repos))
    md = jsonlib.load(TEST_REPOS / 'concepticondata' / 'conceptlists' / 'default-metadata.json')
    md['tables'][0]['url'] = 'Perrin-2010-110.tsv'
    md['tables'][0]['tableSchema']['columns'].extend([dict(name='FRENCH'), dict(name='GERMAN')])
    jsonlib.dump(
        md,
        concepticon_repos / 'concepticondata' / 'conceptlists' / 'Perrin-2010-110.tsv-metadata.json'
    )
    mappings = concepticon_repos / 'mappings'
    mappings.joinpath('map-fr.tsv').write_text("""\
ID\tGLOSS\tPRIORITY
1\tG///the gloss\t2
2\tH///the gloss\t3
3\tH///the gloss\t3
""", encoding='utf8')
    return Concepticon(concepticon_repos)


@pytest.fixture
def dataset(concepticon_api, repos):
    cls = get_dataset_cls(repos / 'concept_set_meta' / 'dsid')
    return cls(
        repos=repos,
        concepticon=concepticon_api,
        mappings={'fr': {
            'the gloss': [('1', 3, 'THING')],
            'other gloss': [('1', 3, 'THING')],
        }})
