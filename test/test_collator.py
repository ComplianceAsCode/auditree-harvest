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
"""Harvest collator tests."""

import tempfile
import unittest
from datetime import datetime
from unittest.mock import MagicMock, call, create_autospec, mock_open, patch

from git import Commit, Remote, Repo

from harvest.collator import Collator


class TestCollator(unittest.TestCase):
    """Test Collator."""

    def setUp(self):
        """Initialize supporting test objects before each test."""
        creds_mock = MagicMock()
        creds_mock.token = 'foo-ghe-token'
        self.creds = {'github': creds_mock}

        self.args = ['https://github.com/foo/bar', self.creds, 'master']

        commit_foo_mock = create_autospec(Commit)
        commit_foo_mock.hexsha = 'foo-hexsha'
        commit_foo_mock.committed_date = datetime(2019, 11, 6).timestamp()
        commit_bar_mock = create_autospec(Commit)
        commit_bar_mock.hexsha = 'bar-hexsha'
        commit_bar_mock.committed_date = datetime(2019, 11, 5).timestamp()
        commit_baz_mock = create_autospec(Commit)
        commit_baz_mock.hexsha = 'baz-hexsha'
        commit_baz_mock.committed_date = datetime(2019, 11, 1).timestamp()
        self.commits = [commit_foo_mock, commit_bar_mock, commit_baz_mock]

    def test_constructor_default(self):
        """Ensures collate object is constructed with default branch."""
        collator = Collator(*self.args)
        self.assertEqual(collator.scheme, 'https')
        self.assertEqual(collator.hostname, 'github.com')
        self.assertEqual(collator.org, 'foo')
        self.assertEqual(collator.repo, 'bar')
        self.assertEqual(collator.creds, self.creds)
        self.assertEqual(collator.branch, 'master')
        self.assertIsNone(collator.repo_path)
        self.assertIsNone(collator.git_repo)

    def test_constructor_with_repo_path(self):
        """Ensures collate object is constructed as expected."""
        collator = Collator(*self.args, 'my/repo/path')
        self.assertEqual(collator.scheme, 'https')
        self.assertEqual(collator.hostname, 'github.com')
        self.assertEqual(collator.org, 'foo')
        self.assertEqual(collator.repo, 'bar')
        self.assertEqual(collator.creds, self.creds)
        self.assertEqual(collator.branch, 'master')
        self.assertEqual(collator.repo_path, 'my/repo/path')
        self.assertIsNone(collator.git_repo)

    def test_read_date_comparison(self):
        """Ensures read returns commits when date logic triggers completion."""
        checkout_mock = MagicMock()
        iter_commits_mock = MagicMock()
        iter_commits_mock.return_value = iter(self.commits)

        collator = Collator(*self.args)
        collator.checkout = checkout_mock
        collator.git_repo = MagicMock()
        collator.git_repo.iter_commits = iter_commits_mock

        commits = collator.read(
            'raw/foo/foo.json', datetime(2019, 11, 4), datetime(2019, 11, 15)
        )
        self.assertEqual(commits, self.commits)
        checkout_mock.assert_called_once()
        actual = iter_commits_mock.call_args_list
        expected = [
            # first call is 00:00 one day later ensuring latest commit returned
            call(
                paths='raw/foo/foo.json',
                until=datetime(2019, 11, 16, 0, 0),
                max_count=1
            ),
            call(
                paths='raw/foo/foo.json',
                until=datetime(2019, 11, 6, 0, 0),
                max_count=1
            ),
            call(
                paths='raw/foo/foo.json',
                until=datetime(2019, 11, 5, 0, 0),
                max_count=1
            )
        ]
        self.assertEqual(len(actual), 3)
        self.assertEqual(actual, expected)

    def test_no_data(self):
        """Ensures read returns commits and exits on StopIteration."""
        checkout_mock = MagicMock()
        iter_commits_mock = MagicMock()
        iter_commits_mock.return_value = iter([])

        collator = Collator(*self.args)
        collator.checkout = checkout_mock
        collator.git_repo = MagicMock()
        collator.git_repo.iter_commits = iter_commits_mock
        with self.assertRaises(ValueError) as cm:
            commits = collator.read(
                'raw/foo/foo.json',
                datetime(2019, 11, 1),
                datetime(2019, 11, 15)
            )
            self.assertEqual(commits, [])
            checkout_mock.assert_called_once()
            actual = iter_commits_mock.call_args_list
            expected = [
                call(
                    paths='raw/foo/foo.json',
                    until=datetime(2019, 11, 15, 0, 0),
                    max_count=1
                )
            ]
            self.assertEqual(len(actual), 1)
            self.assertEqual(actual, expected)
        self.assertEqual(
            str(cm.exception),
            'raw/foo/foo.json not found between 2019-11-01 and 2019-11-15'
        )

    def test_write_functionality(self):
        """Ensures that write is called appropriately."""
        m = mock_open()
        with patch('builtins.open', m):
            collator = Collator(*self.args)
            collator.write('raw/foo/foo.json', self.commits)
        handle = m()

        self.assertEqual(handle.write.call_count, 3)
        self.assertIn(call('./20191106_foo.json', 'w+'), m.mock_calls)
        self.assertIn(call('./20191105_foo.json', 'w+'), m.mock_calls)
        self.assertIn(call('./20191101_foo.json', 'w+'), m.mock_calls)

    @patch('harvest.collator.git.Repo.clone_from')
    @patch('harvest.collator.os.path.isdir')
    def test_checkout_clone(self, is_dir_mock, clone_from_mock):
        """Ensures repo is cloned if none exists."""
        is_dir_mock.return_value = False
        clone_from_mock.return_value = 'my-cloned-repo'

        collator = Collator(*self.args)
        collator.checkout()

        is_dir_mock.assert_called_once_with(
            '/'.join([tempfile.gettempdir(), 'harvest', 'foo', 'bar', '.git'])
        )
        clone_from_mock.assert_called_once_with(
            'https://foo-ghe-token@github.com/foo/bar.git',
            '/'.join([tempfile.gettempdir(), 'harvest', 'foo', 'bar']),
            branch='master'
        )
        self.assertEqual(collator.git_repo, 'my-cloned-repo')

    @patch('harvest.collator.git.Repo', autospec=True)
    @patch('harvest.collator.os.path.isdir')
    def test_checkout_fetch(self, is_dir_mock, repo_mock):
        """Ensures repo is refreshed if repo exists."""
        is_dir_mock.return_value = True
        mock_repo = create_autospec(Repo)
        mock_remote = create_autospec(Remote)
        mock_fetch = MagicMock()
        mock_remote.fetch = mock_fetch
        mock_pull = MagicMock()
        mock_remote.pull = mock_pull
        mock_clone_from = MagicMock()
        mock_remote.clone_from = mock_clone_from
        mock_repo.remote.return_value = mock_remote
        repo_mock.return_value = mock_repo

        collator = Collator(*self.args)
        collator.checkout()

        is_dir_mock.assert_called_once_with(
            '/'.join([tempfile.gettempdir(), 'harvest', 'foo', 'bar', '.git'])
        )
        repo_mock.assert_called_once_with(
            '/'.join([tempfile.gettempdir(), 'harvest', 'foo', 'bar'])
        )
        self.assertEqual(collator.git_repo, mock_repo)
        mock_fetch.assert_called_once_with()
        mock_pull.assert_called_once_with()
        mock_clone_from.assert_not_called()

    @patch('harvest.collator.git.Repo', autospec=True)
    def test_checkout_fetch_repo_path(self, repo_mock):
        """Ensures repo is returned if a local repo path is provided."""
        mock_repo = create_autospec(Repo)
        mock_remote = create_autospec(Remote)
        mock_fetch = MagicMock()
        mock_remote.fetch = mock_fetch
        mock_pull = MagicMock()
        mock_remote.pull = mock_pull
        mock_clone_from = MagicMock()
        mock_remote.clone_from = mock_clone_from
        mock_repo.remote.return_value = mock_remote
        mock_origin = MagicMock()
        mock_origin.url = 'git@github.com:foo/bar.git'
        mock_remotes = MagicMock()
        mock_remotes.origin = mock_origin
        mock_repo.remotes = mock_remotes
        repo_mock.return_value = mock_repo

        collator = Collator(*self.args, 'my/repo/path')
        collator.checkout()

        repo_mock.assert_called_once_with('my/repo/path')
        self.assertEqual(collator.git_repo, mock_repo)
        mock_fetch.assert_not_called()
        mock_pull.assert_not_called()
        mock_clone_from.assert_not_called()

    @patch('harvest.collator.git.Repo', autospec=True)
    def test_checkout_fetch_repo_path_mismatch(self, repo_mock):
        """Ensures exception is raised if repo path does not match org/repo."""
        mock_repo = create_autospec(Repo)
        mock_remote = create_autospec(Remote)
        mock_fetch = MagicMock()
        mock_remote.fetch = mock_fetch
        mock_pull = MagicMock()
        mock_remote.pull = mock_pull
        mock_clone_from = MagicMock()
        mock_remote.clone_from = mock_clone_from
        mock_repo.remote.return_value = mock_remote
        mock_origin = MagicMock()
        mock_origin.url = 'git@github.com:bar/foo.git'
        mock_remotes = MagicMock()
        mock_remotes.origin = mock_origin
        mock_repo.remotes = mock_remotes
        repo_mock.return_value = mock_repo

        collator = Collator(*self.args, 'my/repo/path')
        with self.assertRaises(ValueError) as cm:
            collator.checkout()
            repo_mock.assert_called_once_with('my/repo/path')
            self.assertEqual(collator.git_repo, mock_repo)
            mock_fetch.assert_not_called()
            mock_pull.assert_not_called()
            mock_clone_from.assert_not_called()

        self.assertEqual(str(cm.exception), 'foo/bar repository mismatch')
