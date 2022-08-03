"""
Map a given dataset.
"""
from pyconcepticon import Concepticon

from pynorare.cli_util import add_datasets, iter_datasets


def register(parser):
    add_datasets(parser)


def run(args):
    for dataset in iter_datasets(args):
        dataset.map(concepticon=Concepticon(args.repos.repos))
