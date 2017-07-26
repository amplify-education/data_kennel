data\_kennel
============

Data Kennel is a CLI tool for managing Datadog infrastructure.

About Amplify
=============

Amplify builds innovative and compelling digital educational products
that empower teachers and students across the country. We have a long
history as the leading innovator in K-12 education - and have been
described as the best tech company in education and the best education
company in tech. While others try to shrink the learning experience into
the technology, we use technology to expand what is possible in real
classrooms with real students and teachers.

Learn more at https://www.amplify.com

Getting Started
---------------

Prerequisites
~~~~~~~~~~~~~

Data Kennel requires the following software to be installed: \* python
>= 2.7

For development: \* rake >= 1.9.2

Installing/Building
~~~~~~~~~~~~~~~~~~~

Data Kennel can be installed from pip.

::

    pip install data_kennel

For local development, Data Kennel also includes a setup script in the
form of a rake task.

::

    rake setup:develop

Credentials
~~~~~~~~~~~

Data Kennel expects your Datadog API and APP keys to be available as
environment variables, as ``DATADOG_API_KEY`` and
``DATA_KENNEL_APP_KEY``. Here is an example:

.. code:: bash

    # Data Kennel Envvars
    export DATADOG_API_KEY="change_me"
    export DATA_KENNEL_APP_KEY="change_me"

You can create API and APP keys in the `Datadog
console <https://app.datadoghq.com/account/settings#api>`__.

Running Tests
~~~~~~~~~~~~~

Data Kennel has lint checks and unit tests for use when developing.
Simply run the rake task.

::

    rake test

Supported Operations
====================

Monitor Management
------------------

Data Kennel currently supports listing, syncing, and deleting simple and
composite monitors. Composite monitors are monitors that are composed of
several other monitors. This is achieved through the ``dk_monitor``
command. ``dk_monitor`` has the following options available: \* list \*
update \* delete

See ``dk_monitor -h`` for more information and
``data_kennel.yml.example`` for an example of the configuration file.

Roadmap
=======

-  Add support for ``OR`` boolean operator in composite monitors.
-  Add support for managing Datadog dashboards.
-  Add support for managing Datadog downtimes.
-  Add support for sending arbitrary Datadog events.
-  Add support for queryng arbitrary Datadog metrics.

Responsible Disclosure
======================

If you have any security issue to report, contact project maintainers
privately. You can reach us at github@amplify.com

Contributing
============

We welcome pull requests! For your pull request to be accepted smoothly,
we suggest that you: 1. For any sizable change, first open a GitHub
issue to discuss your idea. 2. Create a pull request. Explain why you
want to make the change and what it’s for. We’ll try to answer any PRs
promptly.
