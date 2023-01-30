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
"""
Bar report fixture for testing purposes.

Other words, blah, blah, detail, blah...
"""

from harvest.reporter import BaseReporter


class BarFixtureReport(BaseReporter):
    """The bar fixture report class."""

    @property
    def report_filename(self):
        """Return the report filename."""
        return "bar_fixture_report.md"

    def generate_report(self):
        """Generate content."""
        return "foo bar baz"
