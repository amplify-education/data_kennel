# pylint: disable=C0302
"""
Tests of data_kennel.monitor
"""
import random

from unittest import TestCase
from mock import MagicMock, call, patch, ANY

from data_kennel.monitor import Monitor
from data_kennel.config import Config


MOCK_TEAM_1 = "mock_team"
MOCK_TEAM_2 = "mock_team2"


MONITORS = []
MOCK_CONFIG = [
    {
        "data_kennel": {
            "team": MOCK_TEAM_1
        },
        "monitors": [
            {
                "name": "mock_monitor for ${foo}",
                "query": "mock_query_${foo}",
                "type": "metric alert",
                "message": "mock_message",
                "notify": [
                    "example@example.com"
                ],
                "tags": {
                    "foo": "${foo}"
                },
                "with_variables": [
                    {
                        "foo": "bar",
                    },
                    {
                        "foo": "foo"
                    }
                ]
            }
        ]
    }
]

MOCK_COMPOSITE_CONFIG_1 = [
    {
        "data_kennel": {
            "team": MOCK_TEAM_1
        },
        "monitors": [
            {
                "name": "mock_composite_monitor for ${foo_1} - ${foo_2}",
                "type": "metric alert",
                "query": "mock_query_${foo_1} "
                         "&& "
                         "mock_query_${foo_2}",
                "message": "mock_message",
                "notify": [
                    "example@example.com"
                ],
                "tags": {
                    "foo_1": "${foo_1}",
                    "foo_2": "${foo_2}"
                },
                "with_variables": [
                    {
                        "foo_1": "bar_1",
                        "foo_2": "bar_2"
                    },
                    {
                        "foo_1": "foo_1",
                        "foo_2": "foo_2"
                    }
                ]
            }
        ]
    }
]

MOCK_COMPOSITE_CONFIG_2 = [
    {
        "data_kennel": {
            "team": MOCK_TEAM_1
        },
        "monitors": [
            {
                "name": "mock_composite_monitor for ${foo_1} - ${foo_2}",
                "type": "metric alert",
                "query": "mock_query_${foo_1} "
                         "&& "
                         "mock_query_${foo_2}",
                "message": "mock_message",
                "notify": [
                    "example@example.com"
                ],
                "options": {
                    "notify_audit": True
                },
                "tags": {
                    "foo_1": "${foo_1}",
                    "foo_2": "${foo_2}"
                },
                "with_variables": [
                    {
                        "foo_1": "bar_1",
                        "foo_2": "bar_2"
                    }
                ]
            }
        ]
    }
]

MOCK_MULTI_CONFIG = [
    {
        "data_kennel": {
            "team": MOCK_TEAM_1
        },
        "monitors": [
            {
                "name": "mock_monitor for ${foo}",
                "query": "mock_query_${foo}",
                "type": "metric alert",
                "message": "mock_message",
                "notify": [
                    "example@example.com"
                ],
                "tags": {
                    "foo": "${foo}"
                },
                "with_variables": [
                    {
                        "foo": "bar",
                    }
                ]
            }
        ]
    },
    {
        "data_kennel": {
            "team": MOCK_TEAM_1
        },
        "monitors": [
            {
                "name": "other_mock_monitor for ${foo}",
                "query": "other_mock_query_${foo}",
                "type": "metric alert",
                "message": "other_mock_message",
                "notify": [
                    "example@example.com"
                ],
                "tags": {
                    "foo": "${foo}"
                },
                "with_variables": [
                    {
                        "foo": "bar",
                    },
                    {
                        "foo": "foo"
                    }
                ]
            }
        ]
    },
    {
        "data_kennel": {
            "team": MOCK_TEAM_2
        },
        "monitors": [
            {
                "name": "mock_composite_monitor for ${foo_1} - ${foo_2}",
                "type": "metric alert",
                "query": "mock_query_${foo_1} "
                         "&& "
                         "mock_query_${foo_2}",
                "message": "mock_message",
                "notify": [
                    "example@example.com"
                ],
                "tags": {
                    "foo_1": "${foo_1}",
                    "foo_2": "${foo_2}"
                },
                "with_variables": [
                    {
                        "foo_1": "bar_1",
                        "foo_2": "bar_2"
                    }
                ]
            }
        ]
    }
]


# While we generally want to patch out the datadog API, there are some tests that don't actually need it
# however. So disable the pylint check for some of those arguments being unused.
# pylint: disable=unused-argument
@patch('datadog.api.Monitor')
class DataKennelMonitorTests(TestCase):
    """Tests of Data Kennel's Monitor"""

    @patch('datadog.initialize', MagicMock())
    def setUp(self):
        self.config1 = Config(config_list=MOCK_CONFIG)
        self.monitor = Monitor(config=self.config1)
        self.composite_config_1 = Config(config_list=MOCK_COMPOSITE_CONFIG_1)
        self.composite_monitor_1 = Monitor(self.composite_config_1)
        self.composite_config_2 = Config(config_list=MOCK_COMPOSITE_CONFIG_2)
        self.composite_monitor_2 = Monitor(self.composite_config_2)
        self.multi_team_config = Config(config_list=MOCK_MULTI_CONFIG)
        self.multi_team_monitor = Monitor(self.multi_team_config)

    def test_list_monitors(self, monitor_api):
        """List monitors has correct format and makes correct calls"""
        tags = [
            'foo:bar',
            'bar:foo',
            'source:data_kennel',
            'team:mock_team',
            'dk_type:Monitor'
        ]

        monitors = [
            {
                'name': 'foo',
                'overall_state': 'mock',
                'tags': tags
            }
        ]

        monitor_api.get_all.return_value = monitors

        actual_list = self.monitor.list()
        expected_list = [
            {
                "Name": "foo",
                "State": "mock",
                "Tags": ", ".join(tags)
            }
        ]

        self.assertEqual(actual_list, expected_list)
        monitor_api.get_all.assert_called_once_with(
            monitor_tags=['source:data_kennel', 'team:mock_team']
        )

    def test_list_composite_monitors(self, monitor_api):
        """
        List simple and composite monitors has correct format and makes correct calls
        and sub-monitors are not showing
        """
        tags = [
            'foo:bar',
            'bar:foo',
            'source:data_kennel',
            'team:mock_team',
            'dk_type:Monitor'
        ]

        sub_monitor_tag = [
            'source:data_kennel',
            'team:mock_team',
            'dk_type:Sub Monitor'
        ]

        monitors = [
            {
                'name': 'foo',
                'overall_state': 'mock',
                'tags': tags
            },
            {
                'name': 'composite monitor',
                'overall_state': 'mock',
                'tags': tags
            },
            {
                'name': 'composite monitor -- 1',
                'overall_state': 'mock',
                'tags': sub_monitor_tag
            },
            {
                'name': 'composite monitor -- 2',
                'overall_state': 'mock',
                'tags': sub_monitor_tag
            }
        ]

        monitor_api.get_all.return_value = monitors

        actual_list = self.monitor.list()
        expected_list = [
            {
                "Name": "foo",
                "State": "mock",
                "Tags": ", ".join(tags)
            },
            {
                "Name": "composite monitor",
                "State": "mock",
                "Tags": ", ".join(tags)

            }
        ]

        self.assertEqual(actual_list, expected_list)
        monitor_api.get_all.assert_called_once_with(
            monitor_tags=['source:data_kennel', 'team:mock_team']
        )

    def test_list_monitors_empty(self, monitor_api):
        """List monitors works with no monitors"""
        monitor_api.get_all.return_value = []

        actual_list = self.monitor.list()
        expected_list = []

        self.assertEqual(actual_list, expected_list)
        monitor_api.get_all.assert_called_once_with(
            monitor_tags=['source:data_kennel', 'team:mock_team']
        )

    def test_update_monitors_creates_monitors(self, monitor_api):
        """Update monitor makes correct calls"""
        self.monitor.update()

        monitor_api.create.assert_has_calls([
            call(
                query="mock_query_bar",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:bar", ANY, "dk_type:Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK] mock_team | mock_monitor for bar"
            ),
            call(
                query="mock_query_foo",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:foo", ANY, "dk_type:Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK] mock_team | mock_monitor for foo"
            ),
        ])
        monitor_api.update.assert_not_called()
        monitor_api.delete.assert_not_called()

    def test_update_creates_composite_monitors(self, monitor_api):
        """Update composite monitor makes correct calls"""
        monitor_bar1 = {'id': 'bar1'}
        monitor_bar2 = {'id': 'bar2'}
        monitor_bar1_bar2 = {'id': 'bar1_bar2'}
        monitor_foo1 = {'id': 'foo1'}
        monitor_foo2 = {'id': 'foo2'}
        monitor_foo1_foo2 = {'id': 'foo1_foo2'}
        monitor_api.create.side_effect = [monitor_bar1, monitor_bar2, monitor_bar1_bar2, monitor_foo1,
                                          monitor_foo2, monitor_foo1_foo2]
        self.composite_monitor_1.update()

        monitor_api.create.assert_has_calls([
            call(
                query="mock_query_bar_1",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 1"
            ),
            call(
                query="mock_query_bar_2",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 2"
            ),
            call(
                query="bar1 && bar2",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["foo_1:bar_1", "foo_2:bar_2", "source:data_kennel", "team:mock_team", ANY,
                      "dk_type:Monitor"],
                type="metric alert",
                name="[DK] mock_team | mock_composite_monitor for bar_1 - bar_2"
            ),
            call(
                query="mock_query_foo_1",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for foo_1 - foo_2 -- 1"
            ),
            call(
                query="mock_query_foo_2",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for foo_1 - foo_2 -- 2"
            ),
            call(
                query="foo1 && foo2",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["foo_1:foo_1", "foo_2:foo_2", "source:data_kennel", "team:mock_team", ANY,
                      "dk_type:Monitor"],
                type="metric alert",
                name="[DK] mock_team | mock_composite_monitor for foo_1 - foo_2"
            )
        ])
        monitor_api.update.assert_not_called()
        monitor_api.delete.assert_not_called()

    def test_creates_composite_monitors_options(self, monitor_api):
        """
        Update composite monitor with options makes correct calls and options are copied in the
        sub-monitors
        """
        monitor_bar1 = {'id': 'bar1'}
        monitor_bar2 = {'id': 'bar2'}
        monitor_bar1_bar2 = {'id': 'bar1_bar2'}
        monitor_api.create.side_effect = [monitor_bar1, monitor_bar2, monitor_bar1_bar2]
        self.composite_monitor_2.update()

        monitor_api.create.assert_has_calls([
            call(
                query="mock_query_bar_1",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 1",
                options={'notify_audit': True}
            ),
            call(
                query="mock_query_bar_2",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 2",
                options={'notify_audit': True}
            ),
            call(
                query="bar1 && bar2",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["foo_1:bar_1", "foo_2:bar_2", "source:data_kennel", "team:mock_team", ANY,
                      "dk_type:Monitor"],
                type="metric alert",
                name="[DK] mock_team | mock_composite_monitor for bar_1 - bar_2",
                options={'notify_audit': True}
            )
        ])
        monitor_api.update.assert_not_called()
        monitor_api.delete.assert_not_called()

    def test_update_creates_multi_team_monitors(self, monitor_api):
        """Update composite monitor makes correct calls"""
        monitor_bar1 = {'id': 'bar1'}
        monitor_bar2 = {'id': 'bar2'}
        monitor_bar1_bar2 = {'id': 'bar1_bar2'}
        monitor_simple_bar1 = {'id': 'simple_bar1'}
        monitor_simple_bar2 = {'id': 'simple_bar2'}
        monitor_simple_foo1 = {'id': 'simple_foo1'}
        monitor_api.create.side_effect = [monitor_bar1, monitor_bar2, monitor_bar1_bar2, monitor_simple_bar1,
                                          monitor_simple_bar2, monitor_simple_foo1]
        self.multi_team_monitor.update()

        monitor_api.create.assert_has_calls([
            call(
                query="mock_query_bar_1",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team2"],
                type="metric alert",
                name="[DK-C] mock_team2 | mock_composite_monitor for bar_1 - bar_2 -- 1"
            ),
            call(
                query="mock_query_bar_2",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team2"],
                type="metric alert",
                name="[DK-C] mock_team2 | mock_composite_monitor for bar_1 - bar_2 -- 2"
            ),
            call(
                query="bar1 && bar2",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["foo_1:bar_1", "foo_2:bar_2", "source:data_kennel", "team:mock_team2", ANY,
                      "dk_type:Monitor"],
                type="metric alert",
                name="[DK] mock_team2 | mock_composite_monitor for bar_1 - bar_2"
            ),
            call(
                query="mock_query_bar",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:bar", ANY, "dk_type:Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK] mock_team | mock_monitor for bar"
            ),
            call(
                query="other_mock_query_bar",
                message="{{#is_alert}}\nother_mock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:bar", ANY, "dk_type:Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK] mock_team | other_mock_monitor for bar"
            ),
            call(
                query="other_mock_query_foo",
                message="{{#is_alert}}\nother_mock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:foo", ANY, "dk_type:Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK] mock_team | other_mock_monitor for foo"
            )
        ])
        monitor_api.update.assert_not_called()
        monitor_api.delete.assert_not_called()

    def test_update_monitors_updates_monitors(self, monitor_api):
        """Update monitors updates already existing monitors"""
        monitors = [
            {
                "name": "[DK] mock_team | mock_monitor for bar",
                "query": "mock_query_bar",
                "extra": "foo-bar",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "foo:bar",
                    "team:mock_team"
                ]
            },
            {
                "name": "[DK] mock_team | mock_monitor for foo",
                "query": "mock_query_foo",
                "extra": "foo-bar",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "foo:foo",
                    "team:mock_team"
                ]
            }
        ]

        monitor_api.get_all.return_value = monitors

        self.monitor.update()

        monitor_api.create.assert_not_called()
        monitor_api.update.assert_has_calls([
            call(
                query="mock_query_bar",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:bar", ANY, "dk_type:Monitor", "team:mock_team"],
                name="[DK] mock_team | mock_monitor for bar",
                type="metric alert",
                extra="foo-bar",
                options={
                    "key": "value"
                }
            ),
            call(
                query="mock_query_foo",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:foo", ANY, "dk_type:Monitor", "team:mock_team"],
                name="[DK] mock_team | mock_monitor for foo",
                type="metric alert",
                extra="foo-bar",
                options={
                    "key": "value"
                }
            ),
        ])
        monitor_api.delete.assert_not_called()

    def test_update_monitors_updates_composite(self, monitor_api):
        """Update monitors updates already existing composite monitors"""
        monitors = [
            {
                "name": "[DK] mock_team | mock_composite_monitor for bar_1 - bar_2",
                "query": "bar_1 && bar_2",
                "extra": "bar1-bar2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "foo_1:bar_1",
                    "foo_2:bar_2",
                    "team:mock_team",
                    "dt_type:Module"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 1",
                "query": "mock_query_bar_1",
                "extra": "bar1-bar2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:Sub Module"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 2",
                "query": "mock_query_bar_2",
                "extra": "bar1-bar2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:SubModule"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for foo_1 - foo_2",
                "query": "foo_1 && foo_2",
                "extra": "foo1-foo2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "foo_1:foo_1",
                    "foo_2:foo_2",
                    "team:mock_team",
                    "dt_type:Module"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for foo_1 - foo_2 -- 1",
                "query": "mock_query_foo_1",
                "extra": "foo1-foo2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:Sub Module"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for foo_1 - foo_2 -- 2",
                "query": "mock_query_foo_2",
                "extra": "foo1-foo2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:SubModule"
                ]
            }
        ]

        monitor_api.get_all.return_value = monitors
        monitor_bar1 = {'id': 'bar_1'}
        monitor_bar2 = {'id': 'bar_2'}
        monitor_bar1_bar2 = {'id': 'bar1_bar2'}
        monitor_foo1 = {'id': 'foo_1'}
        monitor_foo2 = {'id': 'foo_2'}
        monitor_foo1_foo2 = {'id': 'foo1_foo2'}
        monitor_api.update.side_effect = [monitor_bar1, monitor_bar2, monitor_bar1_bar2, monitor_foo1,
                                          monitor_foo2, monitor_foo1_foo2]

        self.composite_monitor_1.update()

        monitor_api.create.assert_not_called()
        monitor_api.update.assert_has_calls([
            call(
                query="mock_query_bar_1",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 1",
                extra="bar1-bar2",
                options={
                    "key": "value"
                }
            ),
            call(
                query="mock_query_bar_2",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 2",
                extra="bar1-bar2",
                options={
                    "key": "value"
                }
            ),
            call(
                query="bar_1 && bar_2",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["foo_1:bar_1", "foo_2:bar_2", "source:data_kennel", "team:mock_team", ANY,
                      "dk_type:Monitor"],
                name="[DK] mock_team | mock_composite_monitor for bar_1 - bar_2",
                type="metric alert",
                extra="bar1-bar2",
                options={
                    "key": "value"
                }
            ),
            call(
                query="mock_query_foo_1",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for foo_1 - foo_2 -- 1",
                extra="foo1-foo2",
                options={
                    "key": "value"
                }
            ),
            call(
                query="mock_query_foo_2",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for foo_1 - foo_2 -- 2",
                extra="foo1-foo2",
                options={
                    "key": "value"
                }
            ),
            call(
                query="foo_1 && foo_2",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["foo_1:foo_1", "foo_2:foo_2", "source:data_kennel", "team:mock_team", ANY,
                      "dk_type:Monitor"],
                name="[DK] mock_team | mock_composite_monitor for foo_1 - foo_2",
                type="metric alert",
                extra="foo1-foo2",
                options={
                    "key": "value"
                }
            ),
        ])
        monitor_api.delete.assert_not_called()

    def test_update_monitors_deletes_monitors(self, monitor_api):
        """Update monitors will delete no longer configured monitors"""
        monitors = [
            {
                "id": 1,
                "name": "fake",
                "query": "fake",
                "tags": [
                    "source:data_kennel",
                    "team:mock_team"
                ]
            }
        ]

        monitor_api.get_all.return_value = monitors

        self.monitor.update()

        monitor_api.create.assert_has_calls([
            call(
                query="mock_query_bar",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:bar", ANY, "dk_type:Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK] mock_team | mock_monitor for bar"
            ),
            call(
                query="mock_query_foo",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["source:data_kennel", "foo:foo", ANY, "dk_type:Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK] mock_team | mock_monitor for foo"
            ),
        ])
        monitor_api.update.assert_not_called()
        monitor_api.delete.assert_called_once_with(1)

    def test_update_monitors_deletes_composite(self, monitor_api):
        """Update monitors will delete no longer configured composite monitors and sub-monitors"""
        monitors = [
            {
                "name": "[DK] mock_team | mock_composite_monitor for bar_1 - bar_2",
                "id": "bar1_bar2",
                "query": "bar_1 && bar_2 && bar_3",
                "extra": "bar1-bar2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "foo_1:bar_1",
                    "foo_2:bar_2",
                    "team:mock_team",
                    "dt_type:Module"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 1",
                "id": "bar1",
                "query": "mock_query_bar_1",
                "extra": "bar1-bar2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:Sub Module"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 2",
                "id": "bar2",
                "query": "mock_query_bar_2",
                "extra": "bar1-bar2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:SubModule"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 3",
                "id": "bar3",
                "query": "mock_query_bar_2",
                "extra": "bar1-bar2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:SubModule"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for xyz_1 - xyz_2",
                "id": "xyz1_xyz2",
                "query": "xyz_1 && xyz_2",
                "extra": "xyz1-xyz2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "foo_1:xyz_1",
                    "foo_2:xyz_2",
                    "team:mock_team",
                    "dt_type:Module"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for xyz_1 - xyz_2 -- 1",
                "id": "xyz1",
                "query": "mock_query_xyz_1",
                "extra": "xyz1-xyz2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:Sub Module"
                ]
            },
            {
                "name": "[DK] mock_team | mock_composite_monitor for xyz_1 - xyz_2 -- 2",
                "id": "xyz2",
                "query": "mock_query_xyz_2",
                "extra": "xyz1-xyz2",
                "options": {
                    "key": "value"
                },
                "tags": [
                    "source:data_kennel",
                    "team:mock_team",
                    "dt_type:SubModule"
                ]
            }
        ]

        monitor_api.get_all.return_value = monitors
        monitor_bar1 = {'id': 'bar_1'}
        monitor_bar2 = {'id': 'bar_2'}
        monitor_bar1_bar2 = {'id': 'bar1_bar2'}
        monitor_foo1 = {'id': 'foo_1'}
        monitor_foo2 = {'id': 'foo_2'}
        monitor_foo1_foo2 = {'id': 'foo1_foo2'}
        monitor_api.update.side_effect = [monitor_bar1, monitor_bar2, monitor_bar1_bar2]
        monitor_api.create.side_effect = [monitor_foo1, monitor_foo2, monitor_foo1_foo2]

        self.composite_monitor_1.update()

        monitor_api.create.assert_has_calls([
            call(
                query="mock_query_foo_1",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for foo_1 - foo_2 -- 1"
            ),
            call(
                query="mock_query_foo_2",
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for foo_1 - foo_2 -- 2"
            ),
            call(
                query="foo_1 && foo_2",
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["foo_1:foo_1", "foo_2:foo_2", "source:data_kennel", "team:mock_team", ANY,
                      "dk_type:Monitor"],
                type="metric alert",
                name="[DK] mock_team | mock_composite_monitor for foo_1 - foo_2"
            )
        ])
        monitor_api.update.assert_has_calls([
            call(
                query="mock_query_bar_1",
                id='bar1',
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 1",
                extra="bar1-bar2",
                options={
                    "key": "value"
                }
            ),
            call(
                query="mock_query_bar_2",
                id='bar2',
                tags=["source:data_kennel", ANY, "dk_type:Sub Monitor", "team:mock_team"],
                type="metric alert",
                name="[DK-C] mock_team | mock_composite_monitor for bar_1 - bar_2 -- 2",
                extra="bar1-bar2",
                options={
                    "key": "value"
                }
            ),
            call(
                query="bar_1 && bar_2",
                id='bar1_bar2',
                message="{{#is_alert}}\nmock_message\n{{/is_alert}}\n{{#is_recovery}}\n"
                        "This alert has recovered.\n{{/is_recovery}}\n@example@example.com",
                tags=["foo_1:bar_1", "foo_2:bar_2", "source:data_kennel", "team:mock_team", ANY,
                      "dk_type:Monitor"],
                name="[DK] mock_team | mock_composite_monitor for bar_1 - bar_2",
                type="metric alert",
                extra="bar1-bar2",
                options={
                    "key": "value"
                }
            )
        ])
        monitor_api.delete.assert_has_calls([
            call('bar3'),
            call('xyz1_xyz2'),
            call('xyz1'),
            call('xyz2')
        ])

    def test_update_dry_run(self, monitor_api):
        """Updating monitors with dry-run does nothing"""
        self.monitor.update(dry_run=True)

        monitor_api.create.assert_not_called()
        monitor_api.update.assert_not_called()
        monitor_api.delete.assert_not_called()

    def test_delete_monitors_works(self, monitor_api):
        """Deleting monitors works"""
        monitors = [
            {
                "name": "Fake monitor 1",
                "id": ''.join(random.choice('1234567890') for _ in range(8)),
                "tags": ["source:data_kennel", "team:mock_team"]
            },
            {
                "name": "Fake monitor 2",
                "id": ''.join(random.choice('1234567890') for _ in range(8)),
                "tags": ["source:data_kennel", "team:mock_team"]
            }
        ]

        monitor_api.get_all.return_value = monitors

        self.monitor.delete()

        monitor_api.delete.assert_has_calls([
            call(monitors[0]['id']),
            call(monitors[1]['id'])
        ])

    def test_delete_monitors_composite(self, monitor_api):
        """Deleting composite monitors  and sub-monitors works"""
        id1 = ''.join(random.choice('1234567890') for _ in range(8))
        id2 = ''.join(random.choice('1234567890') for _ in range(8))
        id3 = ''.join(random.choice('1234567890') for _ in range(8))
        id4 = ''.join(random.choice('1234567890') for _ in range(8))
        monitors = [
            {
                "name": "Fake monitor 1",
                "id": id1,
                "tags": ["source:data_kennel", "team:mock_team", "dt_type:Monitor"],
                "query": "mock query"
            },
            {
                "name": "Fake monitor 2",
                "id": id2,
                "tags": ["source:data_kennel", "team:mock_team", "dt_type:Monitor"],
                "query": id3 + " && " + id4
            },
            {
                "name": "Fake monitor 2 -- 1",
                "id": id3,
                "tags": ["source:data_kennel", "team:mock_team", "dt_type:Sub Monitor"],
                "query": "mock sub query 1"
            },
            {
                "name": "Fake monitor 2 -- 2",
                "id": id4,
                "tags": ["source:data_kennel", "team:mock_team", "dt_type:Sub Monitor"],
                "query": "mock sub query 2"
            }
        ]

        monitor_api.get_all.return_value = monitors
        monitor_api.get.side_effect = [monitors[2], monitors[3]]

        self.monitor.delete()

        monitor_api.delete.assert_has_calls([
            call(monitors[0]['id']),
            call(monitors[1]['id']),
            call(monitors[2]['id']),
            call(monitors[3]['id'])
        ])

    def test_delete_monitors_tag_filtering(self, monitor_api):
        """Deleting monitors works with tag filters"""
        monitors = [
            {
                "name": "Fake monitor 1",
                "id": ''.join(random.choice('1234567890') for _ in range(8)),
                "tags": ["source:data_kennel", "team:mock_team", "foo:bar"],
                "query": "mock query 1"
            },
            {
                "name": "Fake monitor 2",
                "id": ''.join(random.choice('1234567890') for _ in range(8)),
                "tags": ["source:data_kennel", "team:mock_team"],
                "query": "mock query 2"

            }
        ]
        monitor_api.get_all.return_value = monitors

        self.monitor.delete(tags={"foo": "bar"})

        monitor_api.delete.assert_has_calls([
            call(monitors[0]['id'])
        ], any_order=True)

    def test_delete_monitors_works_empty(self, monitor_api):
        """Deleting monitors works with no monitors"""
        self.monitor.delete()

        monitor_api.delete.assert_not_called()

    def test_delete_monitors_dry_run(self, monitor_api):
        """Deleting monitors with dry-run does nothing"""
        monitors = [
            {
                "name": "Fake monitor 1",
                "id": ''.join(random.choice('1234567890') for _ in range(8)),
                "tags": ["source:data_kennel", "team:mock_team"]
            },
            {
                "name": "Fake monitor 2",
                "id": ''.join(random.choice('1234567890') for _ in range(8)),
                "tags": ["source:data_kennel", "team:mock_team"]
            }
        ]

        monitor_api.get_all.return_value = monitors

        self.monitor.delete(dry_run=True)

        monitor_api.delete.assert_not_called()

    def test_compare_monitors_both(self, monitor_api):
        """Comparing monitors by both name and query works"""
        monitor1 = {'name': 'foo', 'query': 'bar'}
        monitor2 = {'name': 'foo', 'query': 'bar'}

        self.assertTrue(self.monitor._compare_monitor(monitor1, monitor2))

    def test_compare_monitors_name(self, monitor_api):
        """Comparing monitors by name works"""
        monitor1 = {'name': 'foo', 'query': 'bar'}
        monitor2 = {'name': 'foo', 'query': 'foobar'}

        self.assertTrue(self.monitor._compare_monitor(monitor1, monitor2))

    def test_compare_monitors_query(self, monitor_api):
        """Comparing monitors by name works"""
        monitor1 = {'name': 'foo', 'query': 'bar'}
        monitor2 = {'name': 'foobar', 'query': 'bar'}

        self.assertTrue(self.monitor._compare_monitor(monitor1, monitor2))

    def test_compare_monitors_both_false(self, monitor_api):
        """Comparing monitors with different name and query fails"""
        monitor1 = {'name': 'bar', 'query': 'bar'}
        monitor2 = {'name': 'foo', 'query': 'foo'}

        self.assertFalse(self.monitor._compare_monitor(monitor1, monitor2))
