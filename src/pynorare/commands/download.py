"""
Map a given dataset.
"""
from pathlib import Path
from importlib.machinery import SourceFileLoader

def register(parser):
    parser.add_argument(
            'dataset',
            nargs='+',
            help='select your dataset',
            type=str)

def run(args):
    for dataset in args.dataset:
        package = SourceFileLoader('norare.'+dataset.replace('-', '_'),
                args.norarepo.joinpath('concept_set_meta', dataset,
                    'map.py').as_posix()).load_module()
        args.log.info('loaded package {0}'.format(package))
        ds = package.Dataset(repos=args.norarepo)
        ds.run([
            'download', 
            ])

