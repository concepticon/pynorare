"""
List all datasets.
"""
from pathlib import Path
from tabulate import tabulate
from importlib.machinery import SourceFileLoader

def run(args):
    
    datasets = []
    for dataset in Path(args.norarepo).glob(
            Path(
                'concept_set_meta',
                '*').as_posix()
            ):
        if dataset.joinpath('map.py').exists():
            package = SourceFileLoader(
                    'norare.'+dataset.name,
                    dataset.joinpath('map.py').as_posix()).load_module()
            ds = package.Dataset(repos=args.norarepo)
            datasets += [[dataset.name, len(ds.columns)]]
    print(tabulate(datasets, headers=['Dataset', 'Columns']))

