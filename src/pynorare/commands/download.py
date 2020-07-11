"""
Download a given dataset.
"""
from pynorare.cli_util import add_datasets, iter_datasets


def register(parser):
    add_datasets(parser)


def run(args):
    for dataset in iter_datasets(args):
        dataset.download()
