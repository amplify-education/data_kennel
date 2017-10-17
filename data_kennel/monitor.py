"""
Data Kennel class for orchestrating management of Datadog monitors.
"""
import logging
import json
import difflib
import random

from datadog import api, initialize

from data_kennel.config import MonitorType
from data_kennel.util import convert_dict_to_tags

logger = logging.getLogger(__name__)


class Monitor(object):
    """
    Class for orchestrating management of Datadog monitors.
    """

    def __init__(self, config=None):
        self.real_monitors = {}
        self.config = config

        initialize(
            api_key=self.config.api_key,
            app_key=self.config.app_key
        )

    def list(self, tags=None):
        """
        Returns a list of dictionarys that forms a human-readable table of monitors created by Data Kennel,
        with optional tags for filtering.
        """
        monitors = self.get_monitors(tags)
        printable_monitors = []

        for monitor in monitors:
            if self._is_principal_monitor(monitor):
                name = monitor['name']
                tags = ", ".join(monitor['tags'])
                state = monitor['overall_state']

                printable_monitors.append(
                    {
                        "Name": name,
                        "State": state,
                        "Tags": tags
                    }
                )

        return printable_monitors

    def update(self, dry_run=False, tags=None):
        """
        Orchestrates creation and updating of monitors. If a configured monitor already exists, it is updated
        in place. If it doesn't exist, then it is created. If an existing monitor has no counterpart in the
        configuration, it is deleted.

        dry_run If True, no changes are written to Datadog.
        tags    A dictionary of tags to filter monitors by.
        """
        logger.info('Updating monitors')

        if dry_run:
            logger.info('--dry-run active, no changes will be made')

        configured_monitors = self.config.get_monitors(tags)
        self.real_monitors = self.get_monitors(tags)

        for configured_monitor in configured_monitors:
            # process sub monitors if the monitor is a composite monitor
            sub_monitors = self.config.get_sub_monitor(configured_monitor)
            sub_monitor_ids = []
            for sub_monitor in sub_monitors:
                monitor = self._create_or_update_monitor(sub_monitor, dry_run)
                sub_monitor_ids.append(monitor['id'])

            if sub_monitor_ids:
                # The monitor is a composite monitor. Build the query using the sub_monitor ids
                configured_monitor['query'] = ' && '.join([str(mon_id) for mon_id in sub_monitor_ids])
                configured_monitor['type'] = 'composite'

            # Process the principal monitor
            self._create_or_update_monitor(configured_monitor, dry_run)

        # For all of the real monitors that didn't have a configured equivalent, delete them.
        for monitor in self.real_monitors:
            logger.info('Deleting monitor: %s', monitor['name'])

            if not dry_run:
                api.Monitor.delete(monitor['id'])

    def delete(self, dry_run=False, tags=None):
        """
        Deletes monitors.

        dry_run If True, no changes are written to Datadog.
        tags    A dictionary of tags to filter monitors by.
        """
        logger.info('Deleting monitors')

        if dry_run:
            logger.info('--dry-run active, no changes will be made')

        monitors = self.get_monitors(tags)

        for monitor in monitors:
            if self._is_principal_monitor(monitor):
                # Process the principal monitor, The sub_monitor will be handle if the monitor is a composite
                logger.info('Deleting monitor: %s', monitor['name'])
                # Try getting any sub_monitors associated to the principal monitor
                sub_monitors = self._get_sub_monitors(monitor)
                if sub_monitors:
                    logger.info('Deleting sub-monitors: %s', [sub_monitor['name'] for sub_monitor in
                                                              sub_monitors])
                if not dry_run:
                    # delete the principal monitor and  any associated sub_monitors
                    api.Monitor.delete(monitor['id'])
                    for sub_monitor_id in [sub_monitor['id'] for sub_monitor in sub_monitors]:
                        api.Monitor.delete(sub_monitor_id)

    def get_monitors(self, tags=None):
        """
        Gets all existing Datadog monitors, with some convenient filtering.

        tags    A dictionary of tags to filter monitors by.
        """
        monitors = []
        # get monitors for each team that we have a config file for
        for team in self.config.teams:
            default_tags = {'source': 'data_kennel', 'team': team}
            default_tags.update(tags or {})
            monitor_tags = convert_dict_to_tags(default_tags)

            monitors.extend(api.Monitor.get_all(monitor_tags=monitor_tags))

        # Annoyingly, the Datadog API treats monitor tags as ORs instead of ANDs, so we need to do some of our
        # own filtering to achieve that behavior.
        # only do the filtering with the actual tags that the user used (exclude the auto team tag
        # since there can be multiple teams)
        user_tags = convert_dict_to_tags(tags or {})
        return [
            monitor for monitor in monitors
            if all(tag in monitor.get('tags', []) for tag in user_tags)
        ]

    def _compare_monitor(self, monitor1, monitor2):
        """
        Convenience method for comparing two monitors.

        If two monitors have the same name or query, they are considered to be equivalent.
        """
        return monitor1['name'] == monitor2['name'] or monitor1['query'] == monitor2['query']

    def _merge_monitor(self, base_monitor, new_monitor):
        """
        Convenience method for merging two monitors.

        The base monitor is updated with the new monitor's configuration.
        """
        monitor = base_monitor.copy()
        monitor.update(new_monitor)

        base_options = base_monitor.get('options', {}).copy()
        base_options.update(new_monitor.get('options', {}))
        monitor['options'] = base_options

        return monitor

    def _diff_monitors(self, monitor1, monitor1_name, monitor2, monitor2_name):
        """
        Convenience method for performing a diff of two monitors, returning the diff as a string.
        """
        return "\n".join(difflib.unified_diff(
            json.dumps(monitor1, indent=4, sort_keys=True).splitlines(),
            json.dumps(monitor2, indent=4, sort_keys=True).splitlines(),
            fromfile=monitor1_name,
            tofile=monitor2_name
        ))

    def _create_or_update_monitor(self, configured_monitor, dry_run=False):
        """
        Function to create or update a monitor
        :param configured_monitor: The monitor to create or update
        :param dry_run: If True, no changes are written to Datadog.
        :return: the created or updated monitor
        """
        real_monitor = next(
            (monitor for monitor in self.real_monitors if self._compare_monitor(monitor, configured_monitor)),
            None
        )

        # If we found an equivalent real_monitor, we prepare to update it. Otherwise, we'll make a new
        # monitor.
        if real_monitor:
            # Its important to play the configured monitor over the real monitor because the config should
            # be considered the source of truth.
            merged_monitor = self._merge_monitor(real_monitor, configured_monitor)
            # The idea is to eventually make real_monitors the list of all real monitors that don't have
            # equivalents in the config.
            self.real_monitors.remove(real_monitor)

            if merged_monitor != real_monitor:
                logger.info('Updating monitor: %s', merged_monitor['name'])

                monitor_diff = self._diff_monitors(
                    real_monitor,
                    "Existing Monitor",
                    merged_monitor,
                    "New Monitor"
                )

                logger.debug('Differences between monitors:\n%s', monitor_diff)

                if not dry_run:
                    return api.Monitor.update(**merged_monitor)

                return merged_monitor
        else:
            logger.info('Creating monitor: %s', configured_monitor['name'])

            if not dry_run:
                return api.Monitor.create(**configured_monitor)

            # If we are making fake monitors for a composite monitor, then we need to insert a fake id for
            # the monitor to have.
            fake_id = ''.join(random.choice('ABCDEF1234567890') for _ in range(12))
            configured_monitor["id"] = fake_id
            return configured_monitor

    def _is_principal_monitor(self, monitor):
        """
        Convenience method for testing if the monitor is a `principal monitor` (not a sub-monitor)
        :param monitor: The monitor
        :return: True if the monitor is a `principal monitor`
        """
        main_monitor_tag = 'dk_type:' + MonitorType.DK_MONITOR
        sub_monitor_tag = 'dk_type:' + MonitorType.DK_SUB_MONITOR

        return main_monitor_tag in monitor['tags'] or sub_monitor_tag not in monitor['tags']

    def _is_composite_monitor(self, monitor):
        """
        Convenience method for testing if the monitor is a `composite monitor`
        :param monitor: The monitor
        :return: True if the monitor is a `composite monitor`
        """
        return ' && ' in monitor.get('query', '')

    def _get_sub_monitors(self, monitor):
        """
        Convenience method for getting the sub-monitor associated to the monitor if the specified monitor
        is a composite monitor
        :param monitor: The monitors
        :return: A list containing the sub-monitors associted to the specified monitor
        """
        sub_monitor_ids = monitor['query'].split('&&') if self._is_composite_monitor(monitor) else []
        sub_monitors = []
        for sub_monitor_id in sub_monitor_ids:
            sub_monitors.append(api.Monitor.get(sub_monitor_id))
        return sub_monitors
