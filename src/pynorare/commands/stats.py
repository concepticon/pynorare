"""
Create statistics for datasets.
"""
from collections import defaultdict

from clldutils.clilib import Table, add_format


def register(parser):
    add_format(parser, default='pipe')
    parser.add_argument(
        '--columns',
        help='list information on columns',
        action='store_true'
    )


def run(args):

    concepts = defaultdict(list)
    for i, ds in enumerate(args.api.datasets.values()):
        args.log.info('analyze ' + ds.id)
        for cid, concept in ds.concepts.items():
            if concept['concepticon_gloss']:
                concepts[cid, concept['concepticon_gloss']] += [ds.id]
    headers = ['No.', 'ID', 'Gloss', 'Datasets']
    with Table(args, *headers) as table:
        for i, ((cid, cgl), clists) in enumerate(
                sorted(concepts.items(), key=lambda x: (len(x[1]), x[0][0]))):
            table.append([i + 1, cid, cgl, len(clists)])
