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
from datetime import datetime, timedelta
from unittest.mock import patch

from harvest.cli import Harvest


class TestHarvestCLICollate(unittest.TestCase):
    """Test Harvest CLI collate sub-command."""

    def setUp(self):
        """Initialize supporting test objects before each test."""
        self.harvest = Harvest()

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_no_dates(self, mock_read, mock_write):
        """Ensures collate sub-command works when no dates provided."""
        mock_read.return_value = ['commit-foo']
        self.harvest.run(
            ['collate', 'https://github.com/foo/bar', 'my/path/baz.json']
        )
        today = datetime.today()

        mock_read.assert_called_once_with(
            'my/path/baz.json',
            datetime(today.year, today.month, today.day),
            datetime(today.year, today.month, today.day)
        )
        mock_write.assert_called_once_with('my/path/baz.json', ['commit-foo'])

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_using_repo_path(self, mock_read, mock_write):
        """Ensures collate sub-command works when no dates provided."""
        mock_read.return_value = ['commit-foo']
        self.harvest.run(
            [
                'collate',
                'https://github.com/foo/bar',
                'my/path/baz.json',
                '--repo-path',
                'os/repo/path'
            ]
        )
        today = datetime.today()

        mock_read.assert_called_once_with(
            'my/path/baz.json',
            datetime(today.year, today.month, today.day),
            datetime(today.year, today.month, today.day)
        )
        mock_write.assert_called_once_with('my/path/baz.json', ['commit-foo'])

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_start_date_only(self, mock_read, mock_write):
        """Ensures collate sub-command works when only start date provided."""
        mock_read.return_value = ['commit-foo', 'commit-bar', 'commit-baz']
        self.harvest.run(
            [
                'collate',
                'https://github.com/foo/bar',
                'my/path/baz.json',
                '--start',
                '20191020'
            ]
        )
        today = datetime.today()
        mock_read.assert_called_once_with(
            'my/path/baz.json',
            datetime(2019, 10, 20),
            datetime(today.year, today.month, today.day)
        )
        mock_write.assert_called_once_with(
            'my/path/baz.json', ['commit-foo', 'commit-bar', 'commit-baz']
        )

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_end_date_only(self, mock_read, mock_write):
        """Ensures collate sub-command works when only end date provided."""
        mock_read.return_value = ['commit-foo', 'commit-bar', 'commit-baz']
        self.harvest.run(
            [
                'collate',
                'https://github.com/foo/bar',
                'my/path/baz.json',
                '--end',
                '20191020'
            ]
        )
        mock_read.assert_called_once_with(
            'my/path/baz.json', datetime(2019, 10, 20), datetime(2019, 10, 20)
        )
        mock_write.assert_called_once_with(
            'my/path/baz.json', ['commit-foo', 'commit-bar', 'commit-baz']
        )

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_both_dates(self, mock_read, mock_write):
        """Ensures collate sub-command works when both dates provided."""
        mock_read.return_value = ['commit-foo', 'commit-bar', 'commit-baz']
        self.harvest.run(
            [
                'collate',
                'https://github.com/foo/bar',
                'my/path/baz.json',
                '--start',
                '20191020',
                '--end',
                '20191120'
            ]
        )
        mock_read.assert_called_once_with(
            'my/path/baz.json', datetime(2019, 10, 20), datetime(2019, 11, 20)
        )
        mock_write.assert_called_once_with(
            'my/path/baz.json', ['commit-foo', 'commit-bar', 'commit-baz']
        )

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_start_eq_end(self, mock_read, mock_write):
        """Ensures collate sub-command works when start date == end date."""
        mock_read.return_value = ['commit-foo', 'commit-bar', 'commit-baz']
        self.harvest.run(
            [
                'collate',
                'https://github.com/foo/bar',
                'my/path/baz.json',
                '--start',
                '20191120',
                '--end',
                '20191120'
            ]
        )
        mock_read.assert_called_once_with(
            'my/path/baz.json', datetime(2019, 11, 20), datetime(2019, 11, 20)
        )
        mock_write.assert_called_once_with(
            'my/path/baz.json', ['commit-foo', 'commit-bar', 'commit-baz']
        )

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_start_gt_end(self, mock_read, mock_write):
        """Ensures collate sub-command fails when start date > end date."""
        self.harvest.run(
            [
                'collate',
                'https://github.com/foo/bar',
                'my/path/baz.json',
                '--start',
                '20191120',
                '--end',
                '20191020'
            ]
        )
        mock_read.assert_not_called()
        mock_write.assert_not_called()

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_future_start(self, mock_read, mock_write):
        """Ensures collate sub-command fails when start date in the future."""
        self.harvest.run(
            [
                'collate',
                'https://github.com/foo/bar',
                'my/path/baz.json',
                '--start',
                (datetime.today() + timedelta(days=1)).strftime('%Y%m%d')
            ]
        )
        mock_read.assert_not_called()
        mock_write.assert_not_called()

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_future_end(self, mock_read, mock_write):
        """Ensures collate sub-command fails when end date in the future."""
        self.harvest.run(
            [
                'collate',
                'https://github.com/foo/bar',
                'my/path/baz.json',
                '--start',
                '20191120',
                '--end',
                (datetime.today() + timedelta(days=1)).strftime('%Y%m%d')
            ]
        )
        mock_read.assert_not_called()
        mock_write.assert_not_called()

    @patch('harvest.collator.Collator.write')
    @patch('harvest.collator.Collator.read')
    def test_collate_local(self, mock_read, mock_write):
        """Ensures collate sub-command works when 'local' repo provided."""
        mock_read.return_value = ['commit-foo']
        self.harvest.run(
            [
                'collate',
                'local',
                'my/path/baz.json',
                '--repo-path',
                'os/repo/path'
            ]
        )
        today = datetime.today()

        mock_read.assert_called_once_with(
            'my/path/baz.json',
            datetime(today.year, today.month, today.day),
            datetime(today.year, today.month, today.day)
        )
        mock_write.assert_called_once_with('my/path/baz.json', ['commit-foo'])
