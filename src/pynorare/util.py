from tqdm import tqdm

def progressbar(iterable=None, **kw):
    kw.setdefault('leave', False)
    kw.setdefault('desc', 'norare')
    return tqdm(iterable=iterable, **kw)


def run(dataset, args):
    if 'download' in args:
        dataset.download()
    if 'map' in args:
        dataset.map_concepts()
