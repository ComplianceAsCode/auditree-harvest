# -*- mode:python; coding:utf-8 -*-
# Copyright (c) 2020 IBM Corp. All rights reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Harvest command line interface."""

import json
import os
from argparse import SUPPRESS
from datetime import datetime

from harvest import __version__ as version
from harvest.collator import Collator
from harvest.utils import (
    get_report_classes,
    get_report_details,
    get_report_module,
    get_report_modules,
    get_report_summary
)

from ilcli import Command

from utilitarian import config_spec, credentials


class _CoreHarvestCommand(Command):

    def _init_arguments(self):
        self.add_argument(
            'org', help='the organization (owner) of a repository'
        )
        self.add_argument(
            'repo', help='the name of a repository within an organization'
        )
        self.add_argument(
            '--repo-path',
            help=(
                'the operating system location of a local git repository - '
                'if not provided, repo will be cloned to $TMPDIR/harvest'
            ),
            metavar='~/path/git-repo',
            default=None
        )
        self.add_argument(
            '--creds',
            metavar='~/path/creds',
            help='the path to credentials file - defaults to %(default)s',
            default='~/.credentials'
        )
        self.add_argument(
            '--no-validate', action='store_false', help=SUPPRESS, default=True
        )


class Collate(_CoreHarvestCommand):
    """Retrieve historical versions of a file from a git repository."""

    name = 'collate'

    def _init_arguments(self):
        super()._init_arguments()
        self.add_argument(
            'filepath',
            help=(
                'the relative path to a file in a git repository '
                'that you wish to retrieve'
            )
        )
        self.add_argument(
            '--end',
            help=(
                'the end of date range for the file you wish to retrieve - '
                'defaults to the current date'
            ),
            metavar='YYYYMMDD',
            default=False
        )
        self.add_argument(
            '--start',
            help=(
                'the start of date range for the file you wish to retrieve - '
                'defaults to same value as the end of date range'
            ),
            metavar='YYYYMMDD',
            default=False
        )

    def _validate_arguments(self, args):
        if not args.end:
            args.end = datetime.today().strftime('%Y%m%d')
        if not args.start:
            args.start = args.end
        args.start = datetime.strptime(args.start, '%Y%m%d')
        args.end = datetime.strptime(args.end, '%Y%m%d')
        if args.start > datetime.today():
            return 'ERROR: start date cannot be in the future'
        if args.start > args.end:
            return 'ERROR: start date cannot be after end date'
        if args.end > datetime.today():
            return 'ERROR: end date cannot be in the future'

    def _run(self, args):
        collator = Collator(
            args.org,
            args.repo,
            credentials.Config(args.creds, spec=config_spec.NullConfigSpec()),
            'master',
            args.repo_path,
            args.no_validate
        )
        try:
            collator.write(
                args.filepath,
                collator.read(args.filepath, args.start, args.end)
            )
        except ValueError as e:
            self.err(f'ERROR: {str(e)}')


class Report(_CoreHarvestCommand):
    """Generate a report based on file content in a git repository."""

    name = 'report'

    def _init_arguments(self):
        super()._init_arguments()
        self.add_argument(
            'package', help='the name of the package that contains the report'
        )
        self.add_argument('name', help='the name of the report to execute')
        self.add_argument(
            '--template-dir',
            help='override path to the report templates folder',
            metavar='~/path/report/templates',
            default=False
        )
        self.add_argument(
            '--config',
            help='key/value pairs needed to execute the report',
            type=json.loads,
            metavar='\'{"key1":"value1","key2":"value2",...}\'',
            default={}
        )

    def _validate_arguments(self, args):
        try:
            rpt_module = get_report_module(args.package, args.name)
        except ModuleNotFoundError:
            return f'ERROR: {args.package} is not found'
        rpts = get_report_classes(rpt_module)
        if not rpts:
            return f'ERROR: {args.name} is not found or is not a valid report'
        if len(rpts) > 1:
            return f'ERROR: {args.name} is ambiguous'
        self.report = rpts[0]
        self.template_dir = args.template_dir or os.path.dirname(
            rpt_module.__file__
        )

    def _run(self, args):
        reporter = self.report(
            args.org,
            args.repo,
            credentials.Config(args.creds, spec=config_spec.NullConfigSpec()),
            'master',
            args.repo_path,
            self.template_dir,
            args.no_validate,
            **args.config
        )
        try:
            reporter.write(reporter.generate_report())
        except (ValueError, RuntimeError) as e:
            self.err(f'ERROR: {str(e)}')


class Reports(Command):
    """Display details about available Harvest reports."""

    name = 'reports'

    def _init_arguments(self):
        self.add_argument('package', help='the package that contains reports')
        self.add_argument(
            '--list',
            help='the summary listing of all harvest reports in the package',
            action='store_true',
            default=False
        )
        self.add_argument(
            '--detail',
            help='the full detailed description for a report',
            metavar='my_report_name',
            default=False
        )

    def _validate_arguments(self, args):
        if not args.detail and not args.list:
            args.list = True

    def _run(self, args):
        if args.list:
            for report in get_report_modules(args.package):
                self.out(
                    f'\n{report.__name__}: '
                    f'{get_report_summary(report) or "N/A"}'
                )
            self.out()
        elif args.detail:
            rpt_module = get_report_module(args.package, args.detail)
            self.out()
            if rpt_module:
                self.out(''.ljust(len(args.detail), '*'))
                self.out(args.detail)
                self.out(''.ljust(len(args.detail), '*'))
                self.out(get_report_details(rpt_module) or 'N/A')
            else:
                self.err(
                    f'ERROR: {args.detail} is not found in {args.package}'
                )


class Harvest(Command):
    """The harvest CLI base command."""

    subcommands = [Collate, Report, Reports]

    def _init_arguments(self):
        self.add_argument(
            '--version',
            help='the harvest version',
            action='version',
            version=f'v{version}'
        )


def run():
    """Execute the harvest CLI."""
    harvest = Harvest()
    exit(harvest.run())


if __name__ == '__main__':
    run()
