'''Utility functions for data kennel'''
from __future__ import print_function

import logging
import sys

from collections import defaultdict

logger = logging.getLogger(__name__)
YES_LIST = ['y', 't', 'yes', 'true', '1']


class EasyExit(Exception):
    """
    Raise this exception to exit your program with a log message and a non-zero status, but no stack trace
    (assuming you are running it with run_gracefully).
    """
    pass


def configure_logging(debug):
    '''Sets the data kennel logger to appropriate levels of chattiness.'''
    default_logger = logging.getLogger('')
    datadog_logger = logging.getLogger('datadog.api')
    requests_logger = logging.getLogger('requests')
    if debug:
        default_logger.setLevel(logging.DEBUG)
        datadog_logger.setLevel(logging.INFO)
        requests_logger.setLevel(logging.INFO)
    else:
        default_logger.setLevel(logging.INFO)
        datadog_logger.setLevel(logging.WARNING)
        requests_logger.setLevel(logging.WARNING)

    stream_handler = logging.StreamHandler(sys.__stdout__)
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s'))
    default_logger.addHandler(stream_handler)


def run_gracefully(main_function):
    """
    Run a "main" function with standardized exception trapping, to make it easy
    to avoid certain unnecessary stack traces.

    If debug logging is switched on, stack traces will return.
    """
    try:
        main_function()
    except EasyExit as msg:
        logger.error(str(msg))
        sys.exit(1)
    except KeyboardInterrupt:
        # swallow the exception unless we turned on debugging, in which case
        # we might want to know what infinite loop we were stuck in
        if logging.getLogger().isEnabledFor(logging.DEBUG):
            raise
        sys.exit(1)


def print_table(rows, headers=None):
    """
    Convenience method for printing a list of dictionary objects into a table. Automatically sizes the
    columns to be the maximum size of any entry in the dictionary, and adds additional buffer whitespace.

    Params:
        rows -                  A list of dictionaries representing a table of information, where keys are the
                                headers of the table. Ex. { 'Name': 'John', 'Age': 23 }

        headers -               A list of the headers to print for the table. Must be a subset of the keys of
                                the dictionaries that compose the row. If a header isn't present or it's value
                                has a falsey value, the value printed is '-'.
    """
    columns_to_sizing = defaultdict(int)
    format_string = ''

    headers = headers or rows[0].keys()

    for row in rows:
        for header in headers:
            value = row.get(header, '-')
            columns_to_sizing[header] = max(len(str(value)), columns_to_sizing[header])

    for header in headers:
        column_size = max(columns_to_sizing[header], len(header)) + 1
        format_string += '{' + header + ':<' + str(column_size) + '}\t'

    print(format_string.format(**{key: key for key in headers}), file=sys.stderr)

    for row in rows:
        defaulted_row = {header: row.get(header) or '-' for header in headers}
        print(format_string.format(**defaulted_row))


def convert_dict_to_tags(tags):
    """Convenience function for converting a dict to datadog tags"""
    return ["{0}:{1}".format(key, value) for key, value in tags.iteritems()]


def convert_tags_to_dict(tags):
    """Convenience function for converting datadog tags to a dict"""
    return dict(tag.split(':', 1) for tag in tags)


def is_truthy(var):
    """Convenience function for checking whether a variable is truthy"""
    if isinstance(var, basestring):
        return var.lower() in YES_LIST
    return bool(var)
