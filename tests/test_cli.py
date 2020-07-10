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
    assert 'a_float' in out
