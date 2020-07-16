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
"""Harvest utilities tests."""

import types
import unittest
from importlib import import_module
from unittest.mock import patch

from harvest.reporter import BaseReporter
from harvest.utils import (
    get_report_classes,
    get_report_details,
    get_report_module,
    get_report_modules,
    get_report_summary
)


class TestUtils(unittest.TestCase):
    """Test harvest utilities."""

    def test_get_report_module(self):
        """Ensure that the correct report module is returned."""
        foo = get_report_module('test.fixtures', 'foo_fixture_report')
        bar = get_report_module('test.fixtures', 'bar_fixture_report')
        self.assertEqual(foo.__name__, 'foo_fixture_report')
        self.assertIsInstance(foo, types.ModuleType)
        self.assertEqual(bar.__name__, 'bar_fixture_report')
        self.assertIsInstance(bar, types.ModuleType)
        self.assertIsNone(get_report_module('test.fixtures', 'not_a_report'))
        self.assertIsNone(get_report_module('test.fixtures', 'no_such_report'))

    def test_get_report_modules(self):
        """Ensures the retrieval of a valid list of report modules."""
        rpt_mods = get_report_modules('test.fixtures')
        for rpt_mod in rpt_mods:
            self.assertIsInstance(rpt_mod, types.ModuleType)
        expected = {'foo_fixture_report', 'bar_fixture_report'}
        self.assertEqual({r.__name__ for r in rpt_mods}, expected)

    def test_get_report_classes(self):
        """Ensures the retrieval of report class(es) based on module name."""
        rpts = get_report_classes(
            import_module('test.fixtures.foo_fixture_report')
        )
        self.assertEqual({r.__name__ for r in rpts}, {'FooFixtureReport'})
        self.assertTrue(issubclass(rpts[0], BaseReporter))
        self.assertEqual(
            get_report_classes(import_module('test.fixtures.not_a_report')), []
        )

    def test_get_report_details(self):
        """Ensures the retrieval of a report module's docstring."""
        rpt_dtls = get_report_details(
            import_module('test.fixtures.foo_fixture_report')
        )
        descr = rpt_dtls.strip('\n').split('\n')
        self.assertEqual(descr[0], 'Foo report fixture for testing purposes.')
        self.assertEqual(descr[-1], 'Other words, blah, blah, detail, blah...')

    def test_get_report_summary(self):
        """Ensures the retrieval of a report module's docstring summary."""
        self.assertEqual(
            get_report_summary(
                import_module('test.fixtures.foo_fixture_report')
            ),
            'Foo report fixture for testing purposes.'
        )

    @patch('harvest.utils.get_report_details')
    def test_get_report_summary_no_details(self, get_report_details_mock):
        """Ensures no summary is returned when no docstring is available."""
        get_report_details_mock.return_value = None
        self.assertIsNone(
            get_report_summary(
                import_module('test.fixtures.foo_fixture_report')
            )
        )
