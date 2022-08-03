import pathlib


def add_datasets(parser):
    parser.add_argument(
        'dataset',
        nargs='+',
        help='select your dataset',
        type=str)


def iter_datasets(args):
    for dsid in args.dataset:
        if pathlib.Path(dsid).exists():
            dsid = pathlib.Path(dsid).name  # pragma: no cover
        yield args.api.datasets[dsid]
