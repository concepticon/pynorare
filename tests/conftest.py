import shutil
import pathlib

import pytest
from pyconcepticon.test_util import get_test_api


@pytest.fixture
def repos(tmpdir):
    shutil.copytree(str(pathlib.Path(__file__).parent / 'repos'), str(tmpdir.join('repos')))
    return pathlib.Path(str(tmpdir)) / 'repos'


@pytest.fixture
def concepticon_api():
    return get_test_api()
