import pathlib

import pytest

from pynorare.__main__ import main


@pytest.fixture
def _main(repos, concepticon_api):
    def f(*args):
        main(['--repos', str(concepticon_api.repos), '--norarepo', str(repos)] + list(args))
    return f


def test_ls(_main, capsys):
    _main('ls')
    out, _ = capsys.readouterr()
    assert 'dsid' in out
    _main('ls', '--columns')
    out, _ = capsys.readouterr()
    assert 'A_FLOAT' in out


def test_stats(_main, capsys):
    _main('stats', '--format=plain')
    out, _ = capsys.readouterr()
    assert out.strip().startswith('No.')


def test_workflow(_main, mocker):
    mocker.patch(
        'pynorare.api.urllib.request',
        mocker.Mock(urlretrieve=lambda u, f: pathlib.Path(f).write_text(
            'gloss,float,int,POS\nthe gloss,1.2,3,noun\nother gloss,1.2,3', encoding='utf8')))
    _main('download', 'dsid')
    _main('map', 'dsid')
    _main('validate', 'dsid')


def test_check(_main):
    _main('check')
