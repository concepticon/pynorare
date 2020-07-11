from pyconcepticon import Concepticon

from pynorare.dataset import get_dataset_cls


def add_datasets(parser):
    parser.add_argument(
        'dataset',
        nargs='+',
        help='select your dataset',
        type=str)


def iter_datasets(args):
    for dsid in args.dataset:
        cls = get_dataset_cls(args.api.datasets[dsid].path.parent)
        yield cls(repos=args.norarepo, concepticon=Concepticon(args.repos.repos))
