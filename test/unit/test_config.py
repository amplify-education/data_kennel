"""
Tests of data_kennel.config
"""
import random
import mock

from unittest import TestCase
from schema import SchemaError

from data_kennel.config import Config


MOCK_API_KEY = "".join(random.choice('1234567890ABCDEF') for _ in range(20))
MOCK_APP_KEY = "".join(random.choice('1234567890ABCDEF') for _ in range(20))

MOCK_TEAM_1 = "mock_team_1"
MOCK_TEAM_2 = "mock_team_2"

MONITORS = []
MOCK_CONFIG = [
    {
        "data_kennel": {
            "team": MOCK_TEAM_1
        },
        "monitors": [
            {
                "name": "mock_monitor for ${foo}",
                "type": "metric alert",
                "query": "mock_query_${foo}",
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

MOCK_COMPOSITE_CONFIG = [
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

MOCK_MULTI_TEAM_CONFIG = [
    {
        "data_kennel": {
            "team": MOCK_TEAM_1
        },
        "monitors": [
            {
                "name": "mock_monitor for ${foo}",
                "type": "metric alert",
                "query": "mock_query_${foo}",
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
    },
    {
        "data_kennel": {
            "team": MOCK_TEAM_1
        },
        "monitors": [
            {
                "name": "other mock_monitor for ${foo}",
                "type": "metric alert",
                "query": "other_mock_query_${foo}",
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


class DataKennelConfigTests(TestCase):
    """Tests of Data Kennel's Config"""

    def setUp(self):
        self.config = Config(
            config_list=MOCK_CONFIG,
            api_key=MOCK_API_KEY,
            app_key=MOCK_APP_KEY
        )
        self.composite_config = Config(
            config_list=MOCK_COMPOSITE_CONFIG,
            api_key=MOCK_API_KEY,
            app_key=MOCK_APP_KEY
        )
        self.multi_team_config = Config(
            config_list=MOCK_MULTI_TEAM_CONFIG,
            api_key=MOCK_API_KEY,
            app_key=MOCK_APP_KEY
        )

    def test_teams(self):
        """Verify team variable read correctly"""
        self.assertEqual(self.multi_team_config.teams, [MOCK_TEAM_1, MOCK_TEAM_2])

    def test_teams_multi(self):
        """Verify team variable read correctly"""
        self.assertEqual(self.config.teams, [MOCK_TEAM_1])

    def test_api_key_overrides_env(self):
        """Verify provided API key is prefered over envvar"""
        self.assertEqual(self.config.api_key, MOCK_API_KEY)

    def test_app_key_overrides_env(self):
        """Verify provided APP key is prefered over envvar"""
        self.assertEqual(self.config.app_key, MOCK_APP_KEY)

    def test_uninterpolated_variable_throws_error(self):
        """Verify monitor not interpolated if unknown variable"""
        bad_config = {
            "data_kennel": {
                "team": MOCK_TEAM_1
            },
            "monitors": [
                {
                    "name": "${bar}",
                    "with_variables": [
                        {
                            "foo": "bar"
                        }
                    ]
                }
            ]
        }

        bad_interpolated_config = self.config._interpolate_config(bad_config)

        self.assertEqual(bad_interpolated_config['monitors'], [])

    def test_interpolation(self):
        """Verify monitor interpolation works correctly"""
        interpolated_config = self.config._interpolate_config(MOCK_CONFIG[0])
        interpolated_monitors = interpolated_config['monitors']

        self.assertEqual(
            [monitor['name'] for monitor in interpolated_monitors],
            ['mock_monitor for bar', 'mock_monitor for foo']
        )

        self.assertEqual(
            [monitor['query'] for monitor in interpolated_monitors],
            ['mock_query_bar', 'mock_query_foo']
        )

    def test_composite_interpolation(self):
        """Verify composite monitor interpolation works correctly"""
        interpolated_config = self.composite_config._interpolate_config(MOCK_COMPOSITE_CONFIG[0])
        interpolated_monitors = interpolated_config['monitors']

        self.assertEqual(
            [monitor['name'] for monitor in interpolated_monitors],
            ['mock_composite_monitor for bar_1 - bar_2', 'mock_composite_monitor for foo_1 - foo_2']
        )

        self.assertEqual(
            [monitor['query'] for monitor in interpolated_monitors],
            ['mock_query_bar_1 && mock_query_bar_2',
             'mock_query_foo_1 && mock_query_foo_2']
        )

    def test_validation(self):
        """Verify config validation fails if config invalid"""
        bad_config = {}

        self.assertRaises(SchemaError, self.config._validate_config, bad_config)

    @mock.patch(
        'os.getenv',
        mock.MagicMock(side_effect=lambda x: 'api' if x == 'DATADOG_API_KEY' else 'app')
    )
    def test_envvar_api_key(self):
        """Verify that API key is read from envvars"""
        config = Config(config_list=MOCK_CONFIG)

        self.assertEqual(config.api_key, 'api')

    @mock.patch(
        'os.getenv',
        mock.MagicMock(side_effect=lambda x: 'api' if x == 'DATADOG_API_KEY' else 'app')
    )
    def test_envvar_app_key(self):
        """Verify that APP key is read from envvars"""
        config = Config(config_list=MOCK_CONFIG)

        self.assertEqual(config.app_key, 'app')

    @mock.patch(
        'os.getenv',
        mock.MagicMock(side_effect=lambda x: None if x == 'DATADOG_API_KEY' else 'app')
    )
    def test_envvar_not_set_api_key(self):
        """Verify exception if API key is not provided"""
        config = Config(config_list=MOCK_CONFIG)

        self.assertRaises(Exception, getattr, config, 'api_key')

    @mock.patch(
        'os.getenv',
        mock.MagicMock(side_effect=lambda x: 'api' if x == 'DATADOG_API_KEY' else None)
    )
    def test_envvar_not_set_app_key(self):
        """Verify exception if APP key is not provided"""
        config = Config(config_list=MOCK_CONFIG)

        self.assertRaises(Exception, getattr, config, 'app_key')
