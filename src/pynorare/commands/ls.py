"""
List all datasets.
"""
from collections import defaultdict

from clldutils.clilib import Table, add_format

from pynorare import NoRaRe
from pynorare.util import progressbar


def register(parser):
    add_format(parser, default='pipe')
    parser.add_argument(
        '--columns',
        help='list information on columns',
        action='store_true'
    )


def run(args):
    norare = NoRaRe(args.norarepo)
    concepts = set()
    columns = defaultdict(list)

    headers = ['No', 'Dataset', 'Field', 'Ln', 'Norare', 'Structure', 'Type'] \
        if args.columns else ['ID', 'Author', 'Year', 'Languages', 'Tags', 'Ratings', 'Concepts']
    with Table(args, *headers) as table:
        for i, ds in progressbar(enumerate(norare.datasets.values())):
            if not args.columns:
                table.append([
                    ds.id,
                    ds.author.replace(' AND ', ' and ').split(' and ')[0],
                    ds.year,
                    ', '.join(ds.source_language[:3]),
                    ', '.join(ds.tags),
                    len(ds.columns) - 3,
                    len(ds.concepts)
                ])
                concepts.update(ds.concepts)
            else:
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
        if not args.columns:
            table.append([
                '-',
                'TOTAL',
                '-',
                '-',
                '-',
                sum([x[-2] for x in table]),
                len(concepts)])
        else:
            for i, (k, v) in enumerate(sorted(columns.items(), key=lambda x: (x[0][1], x[0][0]))):
                table.append((
                    i + 1,
                    k[0],
                    k[1],
                    ', '.join(list(set([x[0] for x in v])))[:30],
                    ', '.join(list(set([x[1] for x in v])))[:15],
                    ', '.join(list(set([x[2] for x in v])))[:15],
                    ', '.join(list(set([x[3] for x in v])))[:15],
                ))
