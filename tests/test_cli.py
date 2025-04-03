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


def make_pretend_data(_url, path):
    data = (
        'gloss,float,int,POS\n'
        'the gloss,1.2,3,noun\n'
        'other gloss,1.2,3')
    pathlib.Path(path).write_text(data, encoding='utf-8')
    return path


def test_workflow(_main, mocker):
    mock_impl = mocker.patch(
        'pynorare.api.files.download_file',
        sideeffect=make_pretend_data)
    _main('download', 'dsid')
    mock_impl.assert_called_once()
    _main('map', 'dsid')
    _main('validate', 'dsid')

    mock_impl = mocker.patch(
        'pynorare.api.files.download_file',
        sideeffect=lambda _url, path: path)
    _main('download', 'ds2')
    mock_impl.assert_called_once()
    _main('map', 'ds2')


def test_errors(_main, capsys):
    _main('download', 'non-existing-dataset')
    _, err = capsys.readouterr()
    assert 'non-existing-dataset' in err
    _main('map', 'non-existing-dataset')
    _, err = capsys.readouterr()
    assert 'non-existing-dataset' in err
    _main('validate', 'non-existing-dataset')
    _, err = capsys.readouterr()
    assert 'non-existing-dataset' in err


def test_check(_main):
    _main('check')
