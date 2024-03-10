# SPDX-FileCopyrightText: 2023-present aaron niskin <aaron@niskin.org>
#
# SPDX-License-Identifier: MIT
import click

from roku.__about__ import __version__
from roku.core import Roku


class CustomMultiCommand(click.Group):
    "stolen from https://stackoverflow.com/a/46721013"

    def command(self, *args, **kwargs):
        """Behaves the same as `click.Group.command()` except if passed
        a list of names, all after the first will be aliases for the first.
        """
        def decorator(f):
            if len(args) > 0 and isinstance(args[0], list):
                fnames = list(args[0])
                if f.__name__ not in fnames:
                    fnames = [f.__name__, *fnames]
                _args = [fnames[0], *list(args[1:])]
                for alias in fnames[1:]:
                    cmd = super(CustomMultiCommand, self).command(
                        alias, *args[1:], **kwargs)(f)
                    cmd.short_help = f"Alias for '{_args[0]}'"
            else:
                _args = args
            cmd = super(CustomMultiCommand, self).command(
                *_args, **kwargs)(f)
            return cmd
        return decorator


@click.group(cls=CustomMultiCommand,
             context_settings={"help_option_names": ["-h", "--help"]},
             invoke_without_command=True)
@click.version_option(version=__version__, prog_name="roku")
@click.option('--debug', '-d', is_flag=True, help='debug mode?')
@click.pass_context
def roku(ctx, debug):
    if ctx.invoked_subcommand is None:
        Roku.find().run(debug=debug)

@roku.command(['v', 'vol'])
@click.argument('direction', type=click.Choice(['u', 'up', 'd', 'down', 'm', 'mute']))
def volume(direction):
    """adjust volume (u)p or (d)own or (m)ute"""
    directions = {
        'u': 'volumeup',
        'd': 'volumedown',
        'm': 'volumemute',
    }
    Roku.find().act(directions[direction[0]])
