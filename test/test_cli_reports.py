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
"""Harvest CLI collate sub-command tests."""

import unittest
from importlib import import_module
from unittest.mock import patch

from harvest.cli import Harvest


class TestHarvestCLIReports(unittest.TestCase):
    """Test Harvest CLI reports sub-command."""

    def setUp(self):
        """Initialize supporting test objects before each test."""
        self.harvest = Harvest()

    @patch('harvest.cli.get_report_summary')
    @patch('harvest.cli.get_report_modules')
    def test_reports(self, mock_rpt_modules, mock_rpt_summary):
        """Ensures reports sub-command works when no options provided."""
        rpt_module = [import_module('test.fixtures.foo_fixture_report')]
        mock_rpt_modules.return_value = rpt_module
        self.harvest.run(['reports', 'test.fixtures'])
        mock_rpt_modules.assert_called_once_with('test.fixtures')
        mock_rpt_summary.assert_called_once_with(rpt_module[0])

    @patch('harvest.cli.get_report_summary')
    @patch('harvest.cli.get_report_modules')
    def test_reports_list(self, mock_rpt_modules, mock_rpt_summary):
        """Ensures reports sub-command works when --list option provided."""
        rpt_module = [import_module('test.fixtures.foo_fixture_report')]
        mock_rpt_modules.return_value = rpt_module
        self.harvest.run(['reports', 'test.fixtures', '--list'])
        mock_rpt_modules.assert_called_once_with('test.fixtures')
        mock_rpt_summary.assert_called_once_with(rpt_module[0])

    @patch('harvest.cli.get_report_details')
    @patch('harvest.cli.get_report_module')
    def test_reports_detail(self, mock_rpt_module, mock_rpt_details):
        """Ensures reports sub-command works when --detail option provided."""
        rpt_module = import_module('test.fixtures.foo_fixture_report')
        mock_rpt_module.return_value = rpt_module
        mock_rpt_details.return_value = ''
        self.harvest.run(
            ['reports', 'test.fixtures', '--detail', 'foo_fixture_report']
        )
        mock_rpt_module.assert_called_once_with(
            'test.fixtures', 'foo_fixture_report'
        )
        mock_rpt_details.assert_called_once_with(rpt_module)

    @patch('harvest.cli.Command.err')
    @patch('harvest.cli.get_report_details')
    @patch('harvest.cli.get_report_module')
    def test_reports_detail_missing(
        self, mock_rpt_module, mock_rpt_details, mock_err
    ):
        """Ensures reports sub-command --detail fails when module not found."""
        mock_rpt_module.return_value = None
        self.harvest.run(
            ['reports', 'test.fixtures', '--detail', 'no_such_report']
        )
        mock_rpt_module.assert_called_once_with(
            'test.fixtures', 'no_such_report'
        )
        mock_rpt_details.assert_not_called()
        mock_err.assert_called_once_with(
            'ERROR: no_such_report is not found in test.fixtures'
        )
