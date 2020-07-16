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
"""Harvest utility functions."""

import inspect
import os
from importlib import import_module
from importlib.util import module_from_spec, spec_from_file_location

from harvest.reporter import BaseReporter


def get_report_module(package, report):
    """
    Retrieve module defined by "report" within the specified "package".

    :param str package: The package that contains the module
    :param str report: The report module name

    :returns: the report module object
    """
    rpt_module_filename = f'{report}.py'
    for dirname, _, files in os.walk(import_module(package).__path__[0]):
        if rpt_module_filename in files:
            file_location = os.path.join(dirname, rpt_module_filename)
            spec = spec_from_file_location(report, file_location)
            module_obj = module_from_spec(spec)
            spec.loader.exec_module(module_obj)
            return module_obj if get_report_classes(module_obj) else None


def get_report_modules(package):
    """
    Retrieve all report modules within the specified "package".

    :param str package: The package that contains the modules

    :returns: a list of report module objects
    """
    rpt_modules = []
    for dirname, _, files in os.walk(import_module(package).__path__[0]):
        for file in files:
            if not file.endswith('.py') or file == '__init__.py':
                continue
            try:
                file_location = os.path.join(dirname, file)
                spec = spec_from_file_location(file[:-3], file_location)
                module_obj = module_from_spec(spec)
                spec.loader.exec_module(module_obj)
            except ImportError:
                continue
            if get_report_classes(module_obj):
                rpt_modules.append(module_obj)
    return rpt_modules


def get_report_classes(report):
    """
    Retrieve the report class objects within the report module.

    :param report: The report module object

    :returns: a list of report class objects found in the report module
    """
    return [
        obj for (name, obj) in inspect.getmembers(report) if (
            inspect.isclass(obj) and issubclass(obj, BaseReporter)
            and name != 'BaseReporter'
        )
    ]


def get_report_details(report):
    """
    Retrieve the docstring content for the given report module.

    :param report: The report module object

    :returns: the docstring for the given report module
    """
    return [
        obj for name, obj in inspect.getmembers(report) if name == '__doc__'
    ][0]


def get_report_summary(report):
    """
    Retrieve the docstring summary content for the given report module.

    :param report: The report module object

    :returns: the first line of the docstring for the given report module
    """
    summary = None
    details = get_report_details(report)
    if not details:
        return
    details = details.split('\n')
    while details and not summary:
        summary = details.pop(0)
    return summary
