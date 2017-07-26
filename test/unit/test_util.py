"""
Tests of data_kennel.util
"""
from unittest import TestCase

from data_kennel.util import (
    convert_dict_to_tags,
    convert_tags_to_dict,
    is_truthy
)


class DataKennelUtilTests(TestCase):
    """Tests of Data Kennel's Utils"""

    def test_dict_to_tags(self):
        """Convert dict to datadog tags"""
        source_dict = {"foo": "bar"}
        expected_tags = ["foo:bar"]
        actual_tags = convert_dict_to_tags(source_dict)
        self.assertEqual(actual_tags, expected_tags)

    def test_tags_to_dict(self):
        """Convert datadog tags to dict"""
        source_tags = ["foo:bar"]
        expected_dict = {"foo": "bar"}
        actual_dict = convert_tags_to_dict(source_tags)
        self.assertEqual(actual_dict, expected_dict)

    def test_is_truthy_true_string(self):
        """Verify that a truthy string is true"""
        self.assertTrue(is_truthy('Yes'))

    def test_is_truthy_false_string(self):
        """Verify that a falsey string is false"""
        self.assertFalse(is_truthy('NOPE'))

    def test_is_truthy_true_bool(self):
        """Verify that a true bool is true"""
        self.assertTrue(is_truthy(True))

    def test_is_truthy_false_bool(self):
        """Verify that a false bool is false"""
        self.assertFalse(is_truthy(False))

    def test_is_truthy_none(self):
        """Verify that None is false"""
        self.assertFalse(is_truthy(None))
