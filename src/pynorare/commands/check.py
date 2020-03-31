"""
Check the norm data TSV file.
"""
from cldfcatalog import Config, Catalog
from pyconcepticon import Concepticon
import tabulate

def run(args, test=False):
    """Check the norm data list"""

    # retrieve the text file
    visited = set()
    table = []
    for clist, cname in args.norms:
        if clist not in args.norms.conceptlists and clist not in visited:
            args.log.info('Missing concept list {0}'.format(clist))
            visited.add(clist)
        elif clist not in visited:
            conceptlist = args.norms.conceptlists[clist]
            if cname not in conceptlist.metadata.tableSchema.columndict:
                args.log.warn('Missing column {1} in conceptlist {0}'.format(
                    clist,
                    cname))
            else:
                # try to retrieve the data and provide some information
                data = [concept.attributes[cname.lower()] for concept in
                        conceptlist.concepts.values() if concept.concepticon_id]
                if args.norms.norms[clist, cname]['DataType'] in ['integer', 'float']:
                    min_, max_ = min(data), max(data)
                else:
                    min_, max_ = '', ''
                table += [[args.norms.norms[clist, cname]['NormDataType'], clist, cname, len(data), len(set(data)), min_,
                    max_]]

    print(tabulate.tabulate(sorted(table, key=lambda x: x[0]), headers=[
        "rating",
        "conceptlist",
        "column",
        "mapped",
        "unique",
        "minimum",
        "maximum"]))

