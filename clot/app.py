"""A simple command-line interface to the clot.torrent package."""


from argparse import ArgumentParser

from clot import __version__


def main():
    """Execute actions according to the command-line arguments."""
    _parse_command_line()


def _parse_command_line():
    parser = ArgumentParser(description=__doc__,
                            prog='python -m clot.app')

    parser.add_argument('--version',
                        action='version',
                        version=f'{__file__} {__version__}')

    parser.parse_args()


if __name__ == '__main__':
    main()
