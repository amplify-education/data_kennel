"""
Class for parsing Data Kennel's configuration file.
"""
import copy
import glob

import os
import re
import json
import logging
import yaml
from schema import Schema, Optional, Or, Use, SchemaError, Regex

from data_kennel.util import convert_dict_to_tags, is_truthy, convert_tags_to_dict
from data_kennel import __version__

DEFAULT_RECOVERY_MESSAGE = "This alert has recovered."
VARIABLE_PATTERN = "(\\$\\{.+?\\})"
SUB_MONITOR_NAME_TEMPLATE = '[DK-C] {0} -- {1}'

VARIABLE_VALIDATOR = Regex(VARIABLE_PATTERN)

CONFIG_SCHEMA = Schema(
    {
        'data_kennel': {
            'team': str
        },
        'monitors': [
            {
                'name': str,
                'query': str,
                'type': Or('metric alert', 'service check', 'event alert', 'query alert'),
                'message': str,
                'notify': [
                    str
                ],
                Optional('tags'): {
                    str: Use(str)
                },
                Optional('with_variables'): [
                    {
                        str: Use(str)
                    }
                ],
                Optional('options'): {
                    Optional('silenced', default=None): {
                        str: Or(None, Use(int))
                    },
                    Optional('notify_no_data'): Or(Use(is_truthy), VARIABLE_VALIDATOR),
                    Optional('new_host_delay'): Or(Use(int), VARIABLE_VALIDATOR),
                    Optional('no_data_timeframe'): Or(Use(int), VARIABLE_VALIDATOR),
                    Optional('timeout_h'): Or(Use(int), VARIABLE_VALIDATOR),
                    Optional('require_full_window'): Or(Use(is_truthy), VARIABLE_VALIDATOR),
                    Optional('renotify_interval'): Or(Use(int), VARIABLE_VALIDATOR),
                    Optional('escalation_message'): str,
                    Optional('notify_audit'): Or(Use(is_truthy), VARIABLE_VALIDATOR),
                    Optional('locked'): Or(Use(is_truthy), VARIABLE_VALIDATOR),
                    Optional('include_tags'): Or(Use(is_truthy), VARIABLE_VALIDATOR),
                    Optional('thresholds'): {
                        Optional('critical'): Or(Use(float), VARIABLE_VALIDATOR),
                        Optional('warning'): Or(Use(float), VARIABLE_VALIDATOR),
                        Optional('ok'): Or(Use(float), VARIABLE_VALIDATOR)
                    },
                    Optional('evaluation_delay'): Or(Use(int), VARIABLE_VALIDATOR),
                    Optional(str): Use(str)
                }
            }
        ]
    }
)

logger = logging.getLogger(__name__)


class MonitorType(object):
    """Enum Class representing the data kennel monitor types"""
    DK_MONITOR = 'Monitor'
    DK_SUB_MONITOR = 'Sub Monitor'


class Config(object):
    """Class for parsing Data Kennel's configuration file."""

    def __init__(self, config_list=None, config_path=None, config_dir=None, api_key=None, app_key=None):
        configs = {}
        self.team_config = {}
        if config_list:
            for config in config_list:
                self._validate_config(config)
                team = config['data_kennel']['team']
                if not configs.get(team):
                    configs[team] = copy.deepcopy(config)
                else:
                    configs[team]['monitors'].extend(config['monitors'])
        elif config_path:
            config = yaml.load(open(config_path))
            self._validate_config(config)
            team = config['data_kennel']['team']
            configs[team] = config
        elif config_dir:
            config_files = glob.glob(config_dir + '/*.yml')
            for conf_file in config_files:
                config = yaml.load(open(conf_file))
                try:
                    self._validate_config(config)
                except SchemaError as ex:
                    raise Exception('Invalid schema in %s: %s' % (conf_file, ex))
                team = config['data_kennel']['team']
                if not configs.get(team):
                    configs[team] = copy.deepcopy(config)
                else:
                    configs[team]['monitors'].extend(config['monitors'])

        self._api_key = api_key
        self._app_key = app_key

        for team in configs:
            self.team_config[team] = self._interpolate_config(configs[team])

    @property
    def teams(self):
        """The teams of the config files"""
        return self.team_config.keys()

    @property
    def api_key(self):
        """Datadog API Key"""
        if self._api_key is None:
            api_key = os.getenv('DATADOG_API_KEY')
            if api_key is None:
                raise Exception('Data Kennel relies on environment variable DATADOG_API_KEY')
            self._api_key = api_key
        return self._api_key

    @property
    def app_key(self):
        """Data Kennel APP Key"""
        if self._app_key is None:
            app_key = os.getenv('DATA_KENNEL_APP_KEY')
            if app_key is None:
                raise Exception('Data Kennel relies on environment variable DATA_KENNEL_APP_KEY')
            self._app_key = app_key
        return self._app_key

    def _get_team(self, config):
        """The team of the config file"""
        return config['data_kennel']['team']

    def _get_team_from_monitor_tags(self, monitor):
        """Extract the team name from the monitor tags"""
        dict_tag = convert_tags_to_dict(monitor['tags'])
        return dict_tag['team']

    def _validate_config(self, config):
        """
        Function for validating that the parsed config object is a valid data_kennel config.
        """
        CONFIG_SCHEMA.validate(config)

    def _build_tags(self, dk_type, team, tags=None):
        """
        Function for building the monitor tags
        :param dk_type: The type of the monitor
        :param team: The Data Kennel Team name
        :param tags: the tags provided in the config file for the monitor
        """
        # Make sure that our default tags are set
        default_tags = {'source': 'data_kennel',
                        'team': team,
                        'dk_version': __version__,
                        'dk_type': dk_type}
        tags = tags or {}
        tags.update(default_tags)
        return tags

    def _interpolate_config(self, config):
        """
        Function for interpolating strings in the config object.

        Returns a copy of the config object with strings interpolated and monitors expanded out.
        """
        interpolated_config = {
            'data_kennel': config['data_kennel'].copy(),
            'monitors': []
        }

        for monitor in config['monitors']:
            variable_sets = monitor.get('with_variables', [{"team": self._get_team(config)}])

            for variable_set in variable_sets:
                variable_set['team'] = self._get_team(config)

                interpolated_monitor = monitor.copy()
                interpolated_monitor.pop('with_variables', None)

                replaces = {re.escape('${{{0}}}'.format(str(k))): str(v) for k, v in variable_set.iteritems()}
                pattern = re.compile("|".join(replaces.keys()))

                # Dumps the complex dictionary into a simple string. Then replace all of our variables with
                # their actual values there.
                interpolated_monitor_string = pattern.sub(
                    lambda m, reps=replaces: reps[re.escape(m.group(0))],
                    json.dumps(interpolated_monitor)
                )

                # If any variables still remain, warn the user but continue.
                matches = re.search(VARIABLE_PATTERN, interpolated_monitor_string)
                if matches is not None:
                    logger.warning(
                        "Non-interpolated variables '%s' found for monitor '%s'",
                        ", ".join(matches.groups()), monitor['name']
                    )
                    continue

                # Load our complex dictionary object back from its string...
                interpolated_monitor = json.loads(interpolated_monitor_string)

                # Build and set the monitor's tags
                interpolated_monitor['tags'] = self._build_tags(MonitorType.DK_MONITOR,
                                                                self._get_team(config),
                                                                interpolated_monitor.get('tags', {}))

                interpolated_config['monitors'].append(interpolated_monitor)

        return interpolated_config

    def get_monitors(self, tags=None):
        """
        Gets monitors in an appropriate format for the Datadog API.

        tags    A dictionary of tags to filter the monitors by.
        """
        configured_monitors = []

        # Tags should really at least be a dict object...
        tags = tags or {}
        # logger.info("team config %s", self.team_config)
        for team in self.teams:
            for monitor in self.team_config[team]['monitors']:
                monitor_tags = monitor.get('tags', {})

                # Test if the requested tags are a subset of the monitor's tags
                if tags.viewitems() <= monitor_tags.viewitems():
                    # Convert tags into the format expected by Datadog's API
                    monitor['tags'] = convert_dict_to_tags(monitor['tags'])

                    # Prefix monitor names with the team name for namespacing
                    monitor['name'] = "[DK] {0} | {1}".format(team, monitor['name'])

                    # Add default recovery message and notificaiton options
                    notifications = " ".join(['@' + notification for notification in monitor['notify']])
                    format_string = (
                        "{{{{#is_alert}}}}\n{0}\n{{{{/is_alert}}}}\n"
                        "{{{{#is_recovery}}}}\n{1}\n{{{{/is_recovery}}}}\n"
                        "{2}"
                    )
                    message = format_string.format(monitor['message'],
                                                   DEFAULT_RECOVERY_MESSAGE,
                                                   notifications)
                    monitor['message'] = message

                    # This isn't needed anymore
                    del monitor['notify']

                    configured_monitors.append(monitor)

        return configured_monitors

    def get_sub_monitor(self, monitor):
        """
        Extract the sub-monitors from the specified monitor in the Datadog format if any exist.
        If the monitor query is a string containing '&&' operator substrings then the monitor is a
        composite monitor and the query elements are the sub-monitor's conditions used by the composite
        monitor.
        :param monitor: The monitor to process
        """
        if isinstance(monitor['query'], basestring) and '&&' not in monitor['query']:
            # The query string does not have any '&&' sub-string, This is a simple monitor
            return {}

        if not isinstance(monitor['query'], basestring):
            # This current version assumes that the query is a string. In the future we will extend Data
            # Kennel to use a list for the query to represent '||' operation
            raise Exception('List in monitor query is not yet supported.')

        sub_monitors = []
        sub_queries = monitor['query'].split('&&')
        index = 1
        name = monitor['name'][len('[DK] '):] if monitor['name'].startswith('[DK] ') else monitor['name']
        tags = convert_dict_to_tags(self._build_tags(dk_type=MonitorType.DK_SUB_MONITOR,
                                                     team=self._get_team_from_monitor_tags(monitor)))

        for query in sub_queries:
            # Create a new monitor for each
            sub_monitor = {
                'name': SUB_MONITOR_NAME_TEMPLATE.format(name, index),
                'type': monitor['type'],
                'tags': tags,
            }
            if monitor.get('options'):
                sub_monitor['options'] = monitor.get('options')
            sub_monitor['query'] = query.strip()
            sub_monitors.append(sub_monitor)
            index += 1

        return sub_monitors
