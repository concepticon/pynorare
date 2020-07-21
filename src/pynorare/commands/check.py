"""
Check the norm data TSV file.
"""


def run(args):
    for i, ds in enumerate(args.api.datasets.values()):
        visited = set()
        args.log.info('checking {0}'.format(ds.id))
        for colid, column in ds.columns.items():
            if colid in args.api.annotations[ds.id]:
                uniq = '-'.join([
                    column.language,
                    column.norare,
                    column.type,
                    column.structure,
                    column.other,
                ])
                if uniq in visited:  # pragma: no cover
                    args.log.warn('non-unique value {0} in {1} / {2}'.format(uniq, ds.id, colid))
                else:
                    visited.add(uniq)
