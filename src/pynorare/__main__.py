"""
Main command line interface to the pyclts package.
"""
import sys
from pathlib import Path
import contextlib

from cldfcatalog import Config, Catalog
from clldutils.clilib import register_subcommands, get_parser_and_subparsers, ParserError
from clldutils.loglib import Logging

from pynorms import Norms

from pyconcepticon import Concepticon


def main(args=None, catch_all=False, parsed_args=None):
    import pynorms.commands

    try:
        repos = Config.from_file().get_clone('concepticon')
    except KeyError:
        repos = Path('.')
    parser, subparsers = get_parser_and_subparsers('speeno')
    parser.add_argument(
        '--repos',
        help="clone of concepticon/concepticon-data",
        default=repos,
        type=Path)
    parser.add_argument(
        '--normfile',
        help="retrieve the file with the norm data",
        default=repos.joinpath('normdata.tsv'),
        type=Path)
    parser.add_argument(
        '--repos-version',
        help="version of repository data. Requires a git clone!",
        default=None)
    register_subcommands(subparsers, pynorms.commands)

    args = parsed_args or parser.parse_args(args=args)
    if not hasattr(args, "main"):
        parser.print_help()
        return 1

    with contextlib.ExitStack() as stack:
        stack.enter_context(Logging(args.log, level=args.log_level))
        if args.repos_version:
            # If a specific version of the data is to be used, we make
            # use of a Catalog as context manager:
            stack.enter_contet(Catalog(args.repos, tag=args.repos_version))
        args.norms = Norms(args.normfile)
        args.repos = Concepticon(args.repos)
        args.log.info('concepticon at {0}'.format(args.repos.repos))
        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except ParserError as e:
            print(e)
            return main([args._command, '-h'])
        except Exception as e:
            if catch_all:  # pragma: no cover
                print(e)
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
