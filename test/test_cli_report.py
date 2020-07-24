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
"""Harvest CLI report sub-command tests."""

import unittest
from unittest.mock import MagicMock, patch

from harvest.cli import Harvest


class TestHarvestCLIReport(unittest.TestCase):
    """Test Harvest CLI report sub-command."""

    def setUp(self):
        """Initialize supporting test objects before each test."""
        self.harvest = Harvest()

        self.mock_generate_report = MagicMock(return_value='foo bar baz')
        self.mock_write_report = MagicMock()
        self.mock_report = MagicMock()
        self.mock_report.generate_report = self.mock_generate_report
        self.mock_report.write = self.mock_write_report
        self.mock_report_class = MagicMock(return_value=self.mock_report)
        self.grm_patcher = patch('harvest.cli.get_report_module')
        self.mock_get_report_module = self.grm_patcher.start()
        self.grc_patcher = patch('harvest.cli.get_report_classes')
        self.mock_get_report_classes = self.grc_patcher.start()

    def tearDown(self):
        """Clean up and house keeping after each test."""
        self.grm_patcher.stop()
        self.grc_patcher.stop()

    def test_validate_pkg_not_found(self):
        """Ensures processing stops when package is not found."""
        self.mock_get_report_module.side_effect = ModuleNotFoundError()
        self.harvest.run(
            [
                'report',
                'https://github.com/foo/bar',
                'no.such.pkg',
                'a_module'
            ]
        )
        self.mock_get_report_module.assert_called_once_with(
            'no.such.pkg', 'a_module'
        )
        self.mock_get_report_classes.assert_not_called()
        self.mock_generate_report.assert_not_called()
        self.mock_write_report.assert_not_called()

    def test_validate_rpt_not_found(self):
        """Ensures processing stops when reports are not found."""
        self.mock_get_report_module.return_value = 'a_module'
        self.mock_get_report_classes.return_value = None
        self.harvest.run(
            [
                'report',
                'https://github.com/foo/bar',
                'a.valid.pkg',
                'a_module'
            ]
        )
        self.mock_get_report_module.assert_called_once_with(
            'a.valid.pkg', 'a_module'
        )
        self.mock_get_report_classes.assert_called_once_with('a_module')
        self.mock_generate_report.assert_not_called()
        self.mock_write_report.assert_not_called()

    def test_validate_rpt_ambiguous(self):
        """Ensures processing stops when more than one report is found."""
        self.mock_get_report_module.return_value = 'a_module'
        self.mock_get_report_classes.return_value = ['rpt1', 'rpt2']
        self.harvest.run(
            [
                'report',
                'https://github.com/foo/bar',
                'a.valid.pkg',
                'a_module'
            ]
        )
        self.mock_get_report_module.assert_called_once_with(
            'a.valid.pkg', 'a_module'
        )
        self.mock_get_report_classes.assert_called_once_with('a_module')
        self.mock_generate_report.assert_not_called()
        self.mock_write_report.assert_not_called()

    @patch('harvest.cli.Command.err')
    def test_validate_rpt_successful(self, mock_err):
        """Ensures report generates successfully."""
        self.mock_get_report_module.return_value = 'a_module'
        self.mock_get_report_classes.return_value = [self.mock_report_class]
        self.harvest.run(
            [
                'report',
                'https://github.com/foo/bar',
                'a.valid.pkg',
                'a_module',
                '--template-dir',
                'meh'
            ]
        )
        self.mock_get_report_module.assert_called_once_with(
            'a.valid.pkg', 'a_module'
        )
        self.mock_get_report_classes.assert_called_once_with('a_module')
        self.mock_generate_report.assert_called_once()
        self.mock_write_report.assert_called_once_with('foo bar baz')
        mock_err.assert_not_called()

    @patch('harvest.cli.Command.err')
    def test_validate_rpt_fails_on_gen(self, mock_err):
        """Ensures report fails on write or generation with error message."""
        self.mock_get_report_module.return_value = 'a_module'
        self.mock_write_report.side_effect = ValueError('boom!')
        self.mock_get_report_classes.return_value = [self.mock_report_class]
        self.harvest.run(
            [
                'report',
                'https://github.com/foo/bar',
                'a.valid.pkg',
                'a_module',
                '--template-dir',
                'meh'
            ]
        )
        self.mock_get_report_module.assert_called_once_with(
            'a.valid.pkg', 'a_module'
        )
        self.mock_get_report_classes.assert_called_once_with('a_module')
        self.mock_generate_report.assert_called_once()
        self.mock_write_report.assert_called_once_with('foo bar baz')
        mock_err.assert_called_once_with('ERROR: boom!')
