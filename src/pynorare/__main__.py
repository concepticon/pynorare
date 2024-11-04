"""
Main command line interface to the pynorare package.
"""
import sys
import pathlib
import contextlib

from cldfcatalog import Config, Catalog
from clldutils.clilib import register_subcommands, get_parser_and_subparsers, ParserError, PathType
from clldutils.loglib import Logging
from pyconcepticon import Concepticon

from pynorare import NoRaRe
from pynorare.util import NoRaReError
import pynorare.commands


def main(args=None, catch_all=False, parsed_args=None):
    try:  # pragma: no cover
        repos = Config.from_file().get_clone('concepticon')
    except KeyError:  # pragma: no cover
        repos = pathlib.Path('.')

    parser, subparsers = get_parser_and_subparsers('norare')
    parser.add_argument(
        '--repos',
        help="clone of concepticon/concepticon-data",
        default=repos,
        type=PathType(type='dir'))
    parser.add_argument(
        '--repos-version',
        help="version of repository data. Requires a git clone!",
        default=None)
    parser.add_argument(
        '--norarepo',
        default=pathlib.Path('.'),
        type=PathType(type='dir'))

    register_subcommands(subparsers, pynorare.commands)

    args = parsed_args or parser.parse_args(args=args)
    if not hasattr(args, "main"):  # pragma: no cover
        parser.print_help()
        return 1

    with contextlib.ExitStack() as stack:
        stack.enter_context(Logging(args.log, level=args.log_level))
        if args.repos_version:  # pragma: no cover
            # If a specific version of the data is to be used, we make
            # use of a Catalog as context manager:
            stack.enter_context(Catalog(args.repos, tag=args.repos_version))
        args.repos = Concepticon(args.repos)
        args.api = NoRaRe(args.norarepo, concepticon=args.repos)
        args.log.info('norare at {0}'.format(args.norarepo))
        try:
            return args.main(args) or 0
        except KeyboardInterrupt:  # pragma: no cover
            return 0
        except ParserError as e:  # pragma: no cover
            print(e)
            return main([args._command, '-h'])
        except NoRaReError as e:
            args.log.error(e)
            return 1
        except Exception as e:  # pragma: no cover
            if catch_all:  # pragma: no cover
                print(e)
                return 1
            raise


if __name__ == '__main__':  # pragma: no cover
    sys.exit(main() or 0)
