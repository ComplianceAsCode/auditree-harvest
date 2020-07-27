[![OS Compatibility][platform-badge]](#prerequisites)
[![Python Compatibility][python-badge]][python-dl]
[![pre-commit][pre-commit-badge]][pre-commit]
[![Code validation](https://github.com/ComplianceAsCode/auditree-harvest/workflows/format%20%7C%20lint%20%7C%20test/badge.svg)][lint-test]
[![Upload Python Package](https://github.com/ComplianceAsCode/auditree-harvest/workflows/PyPI%20upload/badge.svg)][pypi-upload]

# auditree-harvest

The Auditree data gathering and reporting tool.

## Introduction

Auditree `harvest` is a command line tool that assists with the gathering and
formatting of data into human readable reports.  Auditree `harvest` allows
a user to easily retrieve historical raw data, in bulk, from a Git repository
and optionally format that raw data to meet reporting needs.  Auditree
`harvest` is meant to retrieve and report on historical evidence from an
evidence locker.  It is, however, not limited to just processing evidence.  Any
file found in a Git repository hosting service can be processed by Auditree `harvest`.

## Prerequisites

- Supported for execution on OSX and LINUX.
- Supported for execution with Python 3.6 and above.

Python 3 must be installed, it can be downloaded from the [Python][python-dl]
site or installed using your package manager.

Python version can be checked with:

```sh
python --version
```

or

```sh
python3 --version
```

The `harvest` tool is available for download from [PyPI](https://pypi.org/project/auditree-harvest/).

## Installation

It is best practice, but not mandatory, to run `harvest` from a dedicated Python
virtual environment.  Assuming that you have the Python [virtualenv][virtual-env]
package already installed, you can create a virtual environment named `venv` by
executing `virtualenv venv` which will create a `venv` folder at the location of
where you executed the command.  Alternatively you can use the python `venv` module
to do the same.

```sh
python3 -m venv venv
```

Assuming that you have a virtual environment and that virtual environment is in
the current directory then to install a new instance of `harvest`, activate
your virtual environment and use `pip` to install `harvest` like so:

```sh
. ./venv/bin/activate
pip install auditree-harvest
```

As we add functionality to `harvest` users will want to upgrade their `harvest`
package regularly.  To upgrade `harvest` to the most recent version do:

```sh
. ./venv/bin/activate
pip install auditree-harvest --upgrade
```

See [pip documentation][pip-docs] for additional options for using `pip`.

## Configuration

Since Auditree `harvest` interacts with Git repositories, it requires Git remote
hosting service credentials in order to do its thing.  Auditree `harvest` will by
default look for a `username` and `token` in a `~/.credentials` file.  You can
override the credentials file location by using the `--creds` option on a `harvest`
CLI execution. Valid section headings include `github`, `github_enterprise`, `bitbucket`,
and `gitlab`.  Below is an example of the expected credentials entry.

```ini
[github]
username=your-gh-username
token=your-gh-token
```

## Execution

### Collate data

To collate historical versions of a file from a Git repository hosting service
like Github, provide the repository URL (`repo` positional argument), the
relative path to the file within the remote repository including the file name
(`filepath` positional argument) and an optional date range (`--start` and `--end`
arguments).  You can also, optionally, provide the local Git repository path
(`--repo-path` argument), if the repository already exists locally and you wish
to override the remote repository download behavior.

```sh
harvest collate https://github.com/org-foo/repo-bar /raw/baz/baz.json --start 20191201 --end 20191212 --repo-path ./bar-repo
```

- File versions are written to the current local directory where `harvest` was
executed from.
- File versions are prefixed by the commit date in `YYYYMMDD` format.
- File versions are gathered with daily granularity.
   - Only the latest version of a file for a given day is retrieved.
   - If a file did not change on a date then no file version is written for that
   date.  Instead the latest version prior to that date serves as the version of
   that file for that date.
- If you don't provide a `--start` and an `--end` then the latest version of a
file is retrieved.
- If you only provide a `--start` date file versions from the start date to the
current date are retrieved.
- If you only provide an `--end` date the latest version of a file for the end
date is retrieved.

### Generate report(s)

To run a report using content contained in a Git repository hosting service
like Github, provide the repository URL (`repo` positional argument), the report
package (`package`), the report name (`name` positional argument) and include
any configuration that the report requires (`--config`) as a JSON string.  You
can also, optionally, provide the local Git repository path (`--repo-path`
argument), if the repository already exists locally and you wish to override
the remote repository download behavior.

```sh
harvest report https://github.com/org-foo/repo-bar auditree_arboretum check_results_summary --config '{"start":"20191212","end":"20191221"}'
```

#### Getting report details

To see a full summary of available reports within any package (like `auditree-arboretum`) do:

```sh
harvest reports auditree_arboretum --list
```

To see details on a specific report that include usage example do something like:

```sh
harvest reports auditree_arboretum --detail check_results_summary
```

## Report development

Reports should be hosted with the fetchers/checks that collect the evidence for
the reports process. Within `auditree-arboretum` this means the code lives in the
appropriate provider directory.  Contributing common harvest reports are as follows:

1.  Adhere to the auditree-arboretum contribution guidelines - **TODO add link**.
2.  Reports go in the "reports" folder by provider.
3.  Create a python module with a class that extends the [BaseReporter][base-reporter]
class.
    - The `harvest` CLI will use the report module name as the name of the
    report (_sans the .py extention)._
    - **Only one report class per report module is permitted.**
4.  In the new report class the expectations are as follows:
    - Provide a module level docstring that contains:
       - A single line summary
       - A detailed description of the report that includes evidence/files being
       processed and expected configuration
       - At least one usage example
       - Use the [check results summary report docstring][crs-rpt] as an example/template.
       - `harvest` uses this docstring to display available reports and their
       details to the user.
    - Provide/Override the `report_filename` property to return the name of the
    report (including extension).  `harvest` uses this property to apply a report
    template (if desired) and to determine which writer function to use when writing
    the report to a file.  Use the [check results summary report report_filename property][crs-rpt]
    and the [Python packages summary report report_filename property][pps-rpt] as examples.
    - Provide/Override the `generate_report` method.  This is where you put your
    evidence processing and report formatting logic.  Use the
    [check results summary report generate_report][crs-rpt] method as an example.
       - `harvest` takes the optional `--config` command line argument as a JSON
       string when executing a report, converts it to a dictionary and attaches
       it as the `config` attribute to your report object.  Use the report object's
       `config` attribute in the `generate_report` method if you plan to have report
       specific configuration options.
       - Your report object also has a method that retrieves an evidence file for
       a given date. Use the report object's `get_file_content` method when
       retrieving evidence from an evidence locker.
       - Generating CSV reports:
          - `harvest` uses the Python [CSV writer][python-csv] to write out the
          report file. So be sure that your `generate_report` method returns a
          list of dictionaries that adheres to the expectations of the Python
          [CSV writer][python-csv].
       - Generating reports from a Jinja2 template:
          - Add a report template named the same as your `report_filename`
          property with a `.tmpl` extension.  `harvest` will start to look for
          the template in the same directory as the report module.  So as long as
          it exists within that directory structure, `harvest` will find it.
          Use [python_packages_summary.md.tmpl][pps-rpt-tmpl] as an example.
          - `harvest` will look for this template file as part of your report
          processing and, if found, will pass your `generate_report` returned
          content through the template logic.
          - Your `generate_report` returned content should be a dictionary with
          everything necessary for your report template to render the desired
          report appropriately.
          - The report template can access the "raw" content generated by
          `generate_report` through a dictionary named `data` and also has
          access to the report's attributes through the `report` object.
          Use [python_packages_summary.md.tmpl][pps-rpt-tmpl] as an example.
       - Generating reports without templates:
          - You just want to generate report content directly from `generate_report`?
          No problem.  Just generate a string as the report content or a list of
          strings as the rows of the report content and `harvest` will do the rest.

### Custom report development

If you find that you have a specific reporting need that does not fit in as a common
`harvest` report, no problem.  Just develop the report in a separate repo/project
following the same guidelines as above.  As long as the package is importable by
python and you tell `harvest` what package to look for your report(s) in via the CLI,
it will handle the rest.


[changes]: https://github.com/ComplianceAsCode/auditree-harvest/blob/main/CHANGES.md
[platform-badge]: https://img.shields.io/badge/platform-osx%20|%20linux-orange.svg
[python-badge]: https://img.shields.io/badge/python-v3.6+-blue.svg
[python-dl]: https://www.python.org/downloads/
[pip-docs]: https://pip.pypa.io/en/stable/reference/pip/
[virtual-env]: https://pypi.org/project/virtualenv/
[contributing]: https://github.com/ComplianceAsCode/auditree-harvest/blob/main/CONTRIBUTING.md
[base-reporter]: https://github.com/ComplianceAsCode/auditree-harvest/blob/main/harvest/reporter.py
[crs-rpt]: https://github.com/ComplianceAsCode/auditree-harvest/blob/main/auditree_arboretum/provider/auditree/reports/check_results_summary.py
[pps-rpt]: https://github.com/ComplianceAsCode/auditree-harvest/blob/main/auditree_arboretum/provider/auditree/reports/python_packages_summary.py
[python-csv]: https://docs.python.org/3/library/csv.html#csv.writer
[python-io]: https://docs.python.org/3/tutorial/inputoutput.html
[pps-rpt-tmpl]: https://github.com/ComplianceAsCode/auditree-harvest/blob/main/auditree_arboretum/provider/auditree/reports/report_templates/python_packages_summary.md.tmpl
[pre-commit-badge]: https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white
[pre-commit]: https://github.com/pre-commit/pre-commit
[lint-test]: https://github.com/ComplianceAsCode/auditree-harvest/actions?query=workflow%3A%22format+%7C+lint+%7C+test%22
[pypi-upload]: https://github.com/ComplianceAsCode/auditree-harvest/actions?query=workflow%3A%22PyPI+upload%22
