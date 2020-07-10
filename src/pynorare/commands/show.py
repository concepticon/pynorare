"""
Show a dataset with its columns etc.
"""
from tabulate import tabulate
from pynorare import NoRaRe

def register(parser):
    parser.add_argument(
            'dataset',
            nargs=1,
            help='select your dataset',
            type=str)
    parser.add_argument(
            'columns',
            nargs='*',           
            help='show columns',
            type=str
            )
    parser.add_argument(
            '--items',
            default=20,
            help='define number of items',
            type=int
            )

def run(args):
    norare = NoRaRe(repos=args.norarepo)
    if not args.columns:
        columns = norare.get_dataset(args.dataset[0])[1]
    else:
        columns = args.columns
    table = norare.get_columns(args.dataset[0], *columns)
    print(tabulate(table[:args.items], headers=columns, tablefmt='pipe'))
        
