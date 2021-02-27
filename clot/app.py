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

    _add_traversal_arguments_to(parser)
    _add_file_arguments_to(parser)

    return parser.parse_args()


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
    parser.add_argument('--stash',
                        metavar='DIR',
                        help='stash torrents with errors in this directory')


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
        torrent.load(file_path)
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


if __name__ == '__main__':
    main()
