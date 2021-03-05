"""A simple command-line interface to the clot.torrent package."""


from argparse import ArgumentParser
from os import path, walk
import shutil

from clot import __version__, torrent


def main():
    """Execute actions according to the command-line arguments."""
    args = _parse_command_line()

    for source in args.sources:
        if path.isdir(source):
            traverse_dir(source, args)
        elif path.isfile(source):
            handle_file(source, args)
        else:
            if args.verbose:
                print(f'Could not locate file or directory "{source}".')


def _parse_command_line():
    parser = ArgumentParser(description=__doc__,
                            prog='python -m clot.app')

    parser.add_argument('--version',
                        action='version',
                        version=f'{__file__} {__version__}')

    subparsers = parser.add_subparsers(title='subcommands',
                                       required=True,
                                       dest='subcommand',
                                       help='perform specific task on each torrent')
    _add_load_command_to(subparsers)
    _add_dump_command_to(subparsers)

    return parser.parse_args()


def _add_load_command_to(subparsers):
    parser = subparsers.add_parser('load')
    parser.set_defaults(func=_load_torrent)

    _add_traversal_arguments_to(parser)
    _add_file_arguments_to(parser)


def _add_dump_command_to(subparsers):
    parser = subparsers.add_parser('dump')
    parser.set_defaults(func=_dump_torrent)

    _add_traversal_arguments_to(parser)
    _add_file_arguments_to(parser)
    _add_dump_arguments_to(parser)


def _add_traversal_arguments_to(parser):
    parser.add_argument('-v', '--verbose',
                        action='store_true',
                        help='print additional information')

    parser.add_argument('-r', '--recurse',
                        action='store_true',
                        help='recurse into subdirectories')

    parser.add_argument('--follow-links',
                        action='store_true',
                        help='walk down into symbolic links that resolve to directories')

    parser.add_argument('--ext',
                        default='.torrent',
                        help='filter the directories based on filename extension'
                             ' (default: "%(default)s")')

    parser.add_argument('sources',
                        nargs='*',
                        metavar='PATH',
                        default='.',
                        help='torrent file or directory with torrent files'
                             ' (default: current directory)')


def _add_file_arguments_to(parser):
    parser.add_argument('-s', '--stash',
                        metavar='DIR',
                        help='stash torrents with errors in this directory')
    parser.add_argument('--fallback-encoding',
                        help='use this encoding for strings which were not encoded with UTF-8')


def _add_dump_arguments_to(parser):
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--indent',
                       type=int,
                       default=4,
                       help='separate items with newlines and use this number of spaces'
                            ' for indentation (default: %(default)s)')
    group.add_argument('--tab',
                       action='store_const',
                       const='\t',
                       dest='indent',
                       help='separate items with newlines and use tabs for indentation')
    group.add_argument('--no-indent',
                       action='store_const',
                       const=None,
                       dest='indent',
                       help='separate items with spaces rather than newlines')

    parser.add_argument('--sort-keys',
                        action='store_true',
                        help='sort the output of dictionaries alphabetically by key')

    parser.add_argument('-f', '--force',
                        action='store_true',
                        help='overwrite existing files')


def traverse_dir(dir_path, args):
    """Traverse the directory (flat or recursive) and handle files with the specified extension."""
    def onerror(ex):
        print(ex)

    for root, dirs, files in walk(dir_path, onerror=onerror, followlinks=args.follow_links):
        if not args.recurse:
            dirs.clear()

        for name in files:
            if name.endswith(args.ext):
                file_path = path.join(root, name)
                handle_file(file_path, args)


def handle_file(file_path, args):
    """Handle the specified file based on args."""
    if args.verbose:
        print(file_path)

    try:
        obj = torrent.load(file_path, fallback_encoding=args.fallback_encoding)
        args.func(file_path, obj, args)
    except (TypeError, ValueError) as ex:
        if args.stash:
            _stash_file(file_path, args.stash)
        if not args.verbose:
            print(file_path)
        print('\t', repr(ex), sep='')


def _stash_file(file_path, dir_path):
    name, ext = path.splitext(path.basename(file_path))
    target = path.join(dir_path, name + ext)
    suffix = 0
    while path.exists(target):
        suffix += 1
        target = path.join(dir_path, f'{name}-{suffix}{ext}')
    shutil.copy2(file_path, target)


def _load_torrent(file_path, obj, args):  # pylint: disable=unused-argument
    pass


def _dump_torrent(file_path, obj, args):
    obj.dump(file_path + '.json',
             indent=args.indent,
             sort_keys=args.sort_keys,
             overwrite=args.force)


if __name__ == '__main__':
    main()
