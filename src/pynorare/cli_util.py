from pyconcepticon import Concepticon

from pynorare.dataset import NormDataSet


def add_datasets(parser):
    parser.add_argument(
        'dataset',
        nargs='+',
        help='select your dataset',
        type=str)


def iter_datasets(args):
    for dsid in args.dataset:
        yield NormDataSet.from_datasetmeta(
            args.api.datasets[dsid], concepticon=Concepticon(args.repos.repos))
