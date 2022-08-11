"""
List all datasets.
"""
import collections

from clldutils.clilib import Table, add_format

from pynorare.util import progressbar


def register(parser):
    add_format(parser, default='pipe')
    parser.add_argument(
        '--columns',
        help='list information on columns',
        action='store_true'
    )


def run(args):
    concepts = set()
    columns = collections.defaultdict(list)

    headers = ['No', 'Dataset', 'Field', 'Ln', 'Norare', 'Structure', 'Type'] \
        if args.columns else ['ID', 'Author', 'Year', 'Languages', 'Tags', 'Ratings', 'Concepts']
    with Table(args, *headers) as table:
        for i, ds in progressbar(enumerate(args.api.datasets.values())):
            if not args.columns:
                table.append([
                    ds.id,
                    ds.author.replace(' AND ', ' and ').split(' and ')[0],
                    ds.year,
                    ', '.join(ds.source_language[:3]),
                    ', '.join(ds.tags),
                    len(ds.variables),
                    len(ds.concepts)
                ])
                concepts.update(ds.concepts)
            else:
                for var in ds.variables:
                    columns[(ds.id, var.name)] += [(
                        var.language,
                        var.norare,
                        var.structure,
                        var.type,
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
