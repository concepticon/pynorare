from pynorare.util import progressbar


def test_progressbar(capsys):
    for k in progressbar([1, 2, 3]):
        pass
    _, err = capsys.readouterr()
    assert 'norare' in err
