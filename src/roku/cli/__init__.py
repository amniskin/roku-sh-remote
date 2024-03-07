# SPDX-FileCopyrightText: 2023-present aaron niskin <aaron@niskin.org>
#
# SPDX-License-Identifier: MIT
import click

from roku.__about__ import __version__
from roku.core import main


@click.group(context_settings={"help_option_names": ["-h", "--help"]}, invoke_without_command=True)
@click.version_option(version=__version__, prog_name="roku")
@click.option('--debug', '-d', is_flag=True, help='debug mode?')
def roku(**kw):
    main(**kw)
