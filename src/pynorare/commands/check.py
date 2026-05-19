"""
Check the norm data TSV file.
"""


def run(args):
    for ds in args.api.datasets.values():
        visited = set()
        args.log.info(f'checking {ds.id}')
        for column in ds.variables:
            uniq = '-'.join([
                column.language,
                column.norare,
                column.type,
                column.structure,
                column.other,
            ])
            if uniq in visited:  # pragma: no cover
                args.log.warn(f'non-unique value {uniq} in {ds.id} / {column.name}')
            visited.add(uniq)
