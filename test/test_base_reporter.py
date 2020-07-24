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
"""Harvest base reporter tests."""

import csv
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from test.fixtures.bar_fixture_report import BarFixtureReport
from unittest.mock import create_autospec, patch

from git import Blob, Commit

from harvest.exceptions import FileMissingError
from harvest.reporter import BaseReporter

from pkg_resources import resource_filename

TMPLT_DIR = resource_filename('test.fixtures', 'test.fixtures')


class TestBaseReporter(unittest.TestCase):
    """Test BaseReporter."""

    def setUp(self):
        """Initialize supporting test objects before each test."""
        self.args = [
            'https://github.com/org/repo',
            'creds',
            'branch',
            'repo-path',
            TMPLT_DIR
        ]
        self.reporter = BaseReporter(*self.args)

    def test_constructor_with_config(self):
        """Ensures base reporter object is constructed with config."""
        reporter = BaseReporter(*self.args, foo='foo', bar='bar')
        self.assertIsInstance(reporter, BaseReporter)
        self.assertEqual(reporter.repo_url, 'https://github.com/org/repo')
        self.assertEqual(reporter.creds, 'creds')
        self.assertEqual(reporter.branch, 'branch')
        self.assertEqual(reporter.repo_path, 'repo-path')
        self.assertEqual(reporter.template_dir, TMPLT_DIR)
        self.assertEqual(reporter.config, {'foo': 'foo', 'bar': 'bar'})
        self.assertIsNone(reporter.collator)

    def test_constructor_without_config(self):
        """Ensures base reporter object is constructed without config."""
        self.assertIsInstance(self.reporter, BaseReporter)
        self.assertEqual(self.reporter.repo_url, 'https://github.com/org/repo')
        self.assertEqual(self.reporter.creds, 'creds')
        self.assertEqual(self.reporter.branch, 'branch')
        self.assertEqual(self.reporter.repo_path, 'repo-path')
        self.assertEqual(self.reporter.template_dir, TMPLT_DIR)
        self.assertEqual(self.reporter.config, {})
        self.assertIsNone(self.reporter.collator)

    def test_report_filename(self):
        """Ensures report filename property returns the report's filename."""
        self.assertEqual(self.reporter.report_filename, 'BaseReporter.txt')

    @patch('harvest.collator.Collator.read')
    def test_get_file_content_with_date(self, mock_read):
        """Ensures collator called for provided date."""
        blob_mock = create_autospec(Blob)
        blob_mock.data_stream = open('./test/fixtures/rando_output.json', 'r')
        commit_mock = create_autospec(Commit)
        commit_mock.tree = {'/my/file/path': blob_mock}
        mock_read.return_value = [commit_mock]

        file_content = self.reporter.get_file_content(
            '/my/file/path', datetime(2020, 1, 1)
        )
        mock_read.assert_called_once_with(
            '/my/file/path', datetime(2020, 1, 1), datetime(2020, 1, 1)
        )
        self.assertIsNotNone(file_content)

    @patch('harvest.collator.Collator.read')
    def test_get_file_content_no_date(self, mock_read):
        """Ensures collator called for current (default) date."""
        blob_mock = create_autospec(Blob)
        blob_mock.data_stream = open('./test/fixtures/rando_output.json', 'r')
        commit_mock = create_autospec(Commit)
        commit_mock.tree = {'/my/file/path': blob_mock}
        mock_read.return_value = [commit_mock]

        file_content = self.reporter.get_file_content('/my/file/path')
        today = datetime(
            datetime.today().year,
            datetime.today().month,
            datetime.today().day
        )
        mock_read.assert_called_once_with('/my/file/path', today, today)
        self.assertIsNotNone(file_content)

    @patch('harvest.collator.Collator.read')
    def test_get_file_content_future_date(self, mock_read):
        """Ensures collator not called when future date is passed."""
        with self.assertRaises(ValueError) as cm:
            file_content = self.reporter.get_file_content(
                '/my/file/path', datetime.today() + timedelta(days=1)
            )
            mock_read.assert_not_called()
            self.assertIsNone(file_content)
        self.assertTrue(str(cm.exception).endswith('is in the future'))

    @patch('harvest.collator.Collator.read')
    def test_get_file_content_file_not_found(self, mock_read):
        """Ensures nothing is returned when file is not found."""
        mock_read.side_effect = FileMissingError('woopsie')
        file_content = self.reporter.get_file_content(
            '/my/file/path', datetime(2020, 1, 1)
        )
        mock_read.assert_called_once_with(
            '/my/file/path', datetime(2020, 1, 1), datetime(2020, 1, 1)
        )
        self.assertIsNone(file_content)

    @patch('harvest.collator.Collator.read')
    def test_get_file_content_empty(self, mock_read):
        """Ensures nothing is returned if no commits exist for given date."""
        mock_read.return_value = []

        file_content = self.reporter.get_file_content(
            '/my/file/path', datetime(2020, 1, 1)
        )
        mock_read.assert_called_once_with(
            '/my/file/path', datetime(2020, 1, 1), datetime(2020, 1, 1)
        )
        self.assertIsNone(file_content)

    def test_generate_reports(self):
        """Ensures the generate reports method is not implemented."""
        with self.assertRaises(NotImplementedError) as cm:
            self.reporter.generate_report()
        self.assertEqual(
            str(cm.exception), 'Method implemented by sub-classes'
        )

    def test_write_no_content(self):
        """Ensures nothing is written if content is empty."""
        rpt_path = os.path.join(tempfile.gettempdir(), 'BaseReporter.txt')
        self.assertFalse(os.path.exists(rpt_path))
        self.reporter.write('', tempfile.gettempdir())
        self.assertFalse(os.path.exists(rpt_path))

    def test_write_txt_content(self):
        """Ensures text file is written when content provided."""
        rpt_path = os.path.join(tempfile.gettempdir(), 'BaseReporter.txt')
        self.assertFalse(os.path.exists(rpt_path))
        self.reporter.write('foo bar baz', tempfile.gettempdir())
        self.assertTrue(os.path.exists(rpt_path))
        with open(rpt_path, 'r') as f:
            self.assertEqual(f.read(), 'foo bar baz')
        os.remove(rpt_path)

    def test_write_csv_content(self):
        """Ensures csv file is written when content provided."""

        class CSVTestReporter(BaseReporter):

            @property
            def report_filename(self):
                return 'foo.csv'

        reporter = CSVTestReporter(*self.args)
        rpt_path = os.path.join(tempfile.gettempdir(), 'foo.csv')
        self.assertFalse(os.path.exists(rpt_path))
        record = {'FOO': 'foo', 'BAR': 'bar', 'BAZ': 'baz'}
        reporter.write([record], tempfile.gettempdir())
        self.assertTrue(os.path.exists(rpt_path))
        rows = []
        with open(rpt_path, 'r') as f:
            csv_reader = csv.reader(f)
            for row in csv_reader:
                rows.append(row)
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0], ['FOO', 'BAR', 'BAZ'])
        self.assertEqual(rows[1], ['foo', 'bar', 'baz'])
        os.remove(rpt_path)

    def test_write_content_using_template(self):
        """Ensures report is written based on template."""
        reporter = BarFixtureReport(*self.args)
        rpt_path = os.path.join(tempfile.gettempdir(), 'bar_fixture_report.md')
        self.assertFalse(os.path.exists(rpt_path))
        reporter.write('foo bar baz', tempfile.gettempdir())
        self.assertTrue(os.path.exists(rpt_path))
        self.assertTrue(open(rpt_path).read(), '**foo bar baz**')
        os.remove(rpt_path)
