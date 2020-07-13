from tqdm import tqdm


def progressbar(iterable=None, **kw):
    kw.setdefault('leave', False)
    kw.setdefault('desc', 'norare')
    return tqdm(iterable=iterable, **kw)
