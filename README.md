data\_kennel
============

[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3599930cf25b4324a93b6d356bae893b)](https://www.codacy.com/app/CFER/data_kennel?utm_source=github.com&utm_medium=referral&utm_content=amplify-education/data_kennel&utm_campaign=badger)
[![Build Status](https://travis-ci.org/amplify-education/data_kennel.svg?branch=master)](https://travis-ci.org/amplify-education/data_kennel)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://raw.githubusercontent.com/amplify-education/data_kennel/master/LICENSE)
[![PyPi Package](https://badge.fury.io/py/data-kennel.svg)](https://pypi.python.org/pypi/data-kennel)
[![Coverage Badge](https://api.codacy.com/project/badge/Coverage/3599930cf25b4324a93b6d356bae893b)](https://www.codacy.com/app/CFER/data_kennel?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=amplify-education/data_kennel&amp;utm_campaign=Badge_Coverage)
[![Python Versions](https://img.shields.io/pypi/pyversions/data_kennel.svg)](https://pypi.python.org/pypi/data_kennel)

Data Kennel is a CLI tool for managing Datadog infrastructure.

About Amplify
=============

Amplify builds innovative and compelling digital educational products that empower teachers and students across the country. We have a long history as the leading innovator in K-12 education - and have been described as the best tech company in education and the best education company in tech. While others try to shrink the learning experience into the technology, we use technology to expand what is possible in real classrooms with real students and teachers.

Learn more at <https://www.amplify.com>

Getting Started
---------------

### Prerequisites

Data Kennel requires the following software to be installed: 
* python >= 2.7

For development: 
* tox >= 2.9.1

### Installing/Building

Data Kennel can be installed from pip.

    pip install data_kennel

For local development, Data Kennel also includes a setup script.

    python setup.py develop

### Credentials

Data Kennel expects your Datadog API and APP keys to be available as environment variables, as `DATADOG_API_KEY` and `DATA_KENNEL_APP_KEY`. Here is an example:

``` bash
# Data Kennel Envvars
export DATADOG_API_KEY="change_me"
export DATA_KENNEL_APP_KEY="change_me"
```

You can create API and APP keys in the [Datadog console](https://app.datadoghq.com/account/settings#api).

### Running Tests

Data Kennel has lint checks and unit tests for use when developing. Simply run tox.

    tox

Supported Operations
====================

Monitor Management
------------------

Data Kennel currently supports listing, syncing, and deleting simple and composite monitors. Composite monitors are monitors that are composed of several other monitors. This is achieved through the `dk_monitor` command. `dk_monitor` has the following options available: \* list \* update \* delete

See `dk_monitor -h` for more information and `data_kennel.yml.example` for an example of the configuration file.

Roadmap
=======

-   Add support for `OR` boolean operator in composite monitors.
-   Add support for managing Datadog dashboards.
-   Add support for managing Datadog downtimes.
-   Add support for sending arbitrary Datadog events.
-   Add support for queryng arbitrary Datadog metrics.

Responsible Disclosure
======================

If you have any security issue to report, contact project maintainers privately. You can reach us at <github@amplify.com>

Contributing
============

We welcome pull requests! For your pull request to be accepted smoothly, we suggest that you: 1. For any sizable change, first open a GitHub issue to discuss your idea. 2. Create a pull request. Explain why you want to make the change and what it’s for. We’ll try to answer any PRs promptly.
