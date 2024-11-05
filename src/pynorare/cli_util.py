import pathlib

from pynorare.util import NoRaReError


def add_datasets(parser):
    parser.add_argument(
        'dataset',
        nargs='*',
        help='select your dataset',
        type=str)
    parser.add_argument('--start-from', default=None)


def iter_datasets(args):
    if args.dataset:
        desired_datasets = [
            pathlib.Path(dsid).name if pathlib.Path(dsid).exists() else dsid
            for dsid in args.dataset]
    else:
        desired_datasets = args.api.datasets
    if args.start_from:
        desired_datasets = [
            dsid
            for dsid in desired_datasets
            if dsid >= args.start_from]

    unknown_datasets = [
        dsid
        for dsid in desired_datasets
        if dsid not in args.api.datasets]
    if unknown_datasets:
        raise NoRaReError(
            'Unknown dataset(s): {}'.format(', '.join(unknown_datasets)))

    for dsid in desired_datasets:
        ds = args.api.datasets[dsid]
        ds.log = args.log
        yield ds
