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
            table += [[i+1, ds.author.replace(' AND ', ' and ').split(' and ')[0], ds.year,
                ', '.join(ds.source_language[:3]), ', '.join(ds.tags),
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
        columns = defaultdict(list)
        for i, ds in tqdm(enumerate(norare.datasets.values())):
            for column in ds.columns:
                if column not in [
                    'concepticon_id',
                    'concepticon_gloss',
                    'line_in_source',
                    'english',
                    'german',
                    'polish',
                    'spanish',
                    'chinese',
                    'french',
                    'dutch',
                    ]:
                    columns[(ds.id, column)] += [(
                        ds.columns[column].language, 
                        ds.columns[column].norare,
                        ds.columns[column].structure,
                        ds.columns[column].type,

                        )]

        table = []
        for i, (k, v) in enumerate(sorted(columns.items(),
            key=lambda x: (x[0][1], x[0][0]))):
            table += [(
                i+1, 
                k[0],
                k[1],
                ', '.join(list(set([x[0] for x in v])))[:30],
                ', '.join(list(set([x[1] for x in v])))[:15],
                ', '.join(list(set([x[2] for x in v])))[:15],
                ', '.join(list(set([x[3] for x in v])))[:15],

                )
                ]
        print(tabulate(table, headers=['No', 
            'Dataset', 'Field', 'Ln', 'Norare', 'Structure', 'Type']))


    

