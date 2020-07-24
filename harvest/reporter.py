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
"""Harvest reporter base class module."""

import csv
import os
from datetime import datetime

from harvest.collator import Collator
from harvest.exceptions import FileMissingError

from jinja2 import Environment, FileSystemLoader


class BaseReporter(object):
    """Base reporter class.  All reports must be sub-classes of this class."""

    def __init__(
        self,
        repo_url,
        creds,
        branch,
        repo_path=None,
        template_dir=None,
        validate=True,
        **config
    ):
        """Construct the reporter object."""
        self.repo_url = repo_url
        self.creds = creds
        self.branch = branch
        self.repo_path = repo_path
        self.template_dir = template_dir
        self.validate = validate
        self.config = config
        self.collator = None

    @property
    def report_filename(self):
        """Override in sub-class to an appropriate filename."""
        return f'{self.__class__.__name__}.txt'

    def get_file_content(self, filepath, file_dt=None):
        """
        Retrieve file content for a given file and date from a git repository.

        :param str filepath: The relative path to the file within the repo
        :param datetime file_dt: The date of the file version

        :returns: The file content
        """
        if not self.collator:
            self.collator = Collator(
                self.repo_url,
                self.creds,
                self.branch,
                self.repo_path,
                self.validate
            )
        if not file_dt:
            file_dt = datetime.today()
        if file_dt > datetime.today():
            raise ValueError(
                f'{file_dt.strftime("%Y-%m-%d")} is in the future'
            )
        commits = None
        try:
            commits = self.collator.read(
                filepath,
                datetime(file_dt.year, file_dt.month, file_dt.day),
                datetime(file_dt.year, file_dt.month, file_dt.day)
            )
        except FileMissingError:
            pass
        return (
            commits[0].tree[filepath].data_stream.read() if commits else None
        )

    def generate_report(self):
        """Stub method for custom report generation by sub-classes."""
        raise NotImplementedError('Method implemented by sub-classes')

    def write(self, raw_content, location='.'):
        """
        Create report artifact.

        :param raw_content: The raw content as a list of strings or a string
        """
        if not raw_content:
            return
        rpt_content = self._format_content(raw_content)
        with open(os.path.join(location, self.report_filename), 'w+') as f:
            write_func = f.write
            is_csv = self.report_filename.rsplit('.', 1).pop().lower() == 'csv'
            if is_csv and isinstance(rpt_content, list):
                csv_writer = csv.DictWriter(
                    f, fieldnames=rpt_content[0].keys()
                )
                csv_writer.writeheader()
                write_func = csv_writer.writerow
            if isinstance(rpt_content, list):
                for row in rpt_content:
                    write_func(row)
            else:
                write_func(rpt_content)

    def _format_content(self, raw_content):
        template_env = None
        template_file = f'{self.report_filename}.tmpl'
        for dirname, _, files in os.walk(self.template_dir):
            if template_file in files:
                template_env = Environment(
                    loader=FileSystemLoader(searchpath=dirname),
                    trim_blocks=True,
                    lstrip_blocks=True,
                    autoescape=True
                )
                break
        if not template_env:
            return raw_content
        template = template_env.get_template(template_file)
        return template.render(data=raw_content, report=self)
