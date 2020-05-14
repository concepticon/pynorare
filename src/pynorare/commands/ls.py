"""
List all datasets.
"""
from pathlib import Path
from tabulate import tabulate
from pynorare.norare import NoRaRe
from tqdm import tqdm
from collections import defaultdict

def register(parser):
    parser.add_argument(
            '--datasets',
            help='list information on datasets',
            action='store_true'
            )
    parser.add_argument(
            '--columns',
            help='list information on columns',
            action='store_true'
            )

def run(args):

    norare = NoRaRe(args.norarepo)
    concepts = set()
    if args.datasets:
        table = []
        for i, ds in tqdm(enumerate(norare.datasets.values())):
            table += [[i+1, ds.author.split(' and ')[0], ds.year,
                ds.source_language, ', '.join(ds.tags),
                len(ds.columns)-3, len(ds.concepts)]]
            concepts.update(ds.concepts)
        table += [[
            '-',
            'TOTAL',
            '-',
            '-',
            '-',
            sum([x[-2] for x in table]),
            len(concepts)]]
        print(tabulate(table, headers=['Author', 'Year', 'Languages', 'Tags', 'Ratings', 'Concepts'], 
            tablefmt='pipe'))

    if args.columns:
        columns = defaultdict(int)
        for i, ds in tqdm(enumerate(norare.datasets.values())):
            for column in ds.columns:
                if column not in [
                    'concepticon_id',
                    'concepticon_gloss',
                    'line_in_source'
                    ]:
                    columns[column] += 1

        table = []
        for i, (k, v) in enumerate(sorted(columns.items(),
            key=lambda x: x[1], reverse=True)):
            table += [(i+1, k, v)]
        print(tabulate(table))


    

