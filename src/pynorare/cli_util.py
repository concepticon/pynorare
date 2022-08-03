import pathlib


def add_datasets(parser):
    parser.add_argument(
        'dataset',
        nargs='*',
        help='select your dataset',
        type=str)
    parser.add_argument('--start-from', default=None)


def iter_datasets(args):
    dsids = [
        pathlib.Path(dsid).name if pathlib.Path(dsid).exists() else dsid for dsid in args.dataset]
    for dsid, ds in sorted(args.api.datasets.items(), key=lambda i: i[0]):
        if args.start_from and dsid < args.start_from:
            continue  # pragma: no cover
        if (not dsids) or dsid in dsids:
            ds.log = args.log
            yield ds
