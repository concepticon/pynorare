"""
Check the norm data TSV file.
"""
from cldfcatalog import Config, Catalog
from pyconcepticon import Concepticon
import tabulate
from pynorare import NoRaRe

def run(args, test=False):
    """Check the norm data list"""

    # retrieve the text file
    norare = NoRaRe(args.norarepo)
    for i, ds in enumerate(norare.datasets.values()):
        visited = set()
        args.log.info('checking {0}'.format(ds.id))
        for colid, column in ds.columns.items():
            if colid in norare.annotations[ds.id]:
                uniq = '-'.join([column.language, column.norare,
                    column.type, column.structure, column.other])
                if uniq in visited:
                    args.log.warn('non-unique value {0} in {1} / {2}'.format(
                        uniq,
                        ds.id,
                        colid))
                else:
                    visited.add(uniq)

