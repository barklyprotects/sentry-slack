from __future__ import absolute_import

import responses

from exam import fixture
from sentry.models import Rule
from sentry.plugins import Notification
from sentry.testutils import TestCase
from sentry.utils import json
from urlparse import parse_qs

from sentry_slack.plugin import SlackPlugin


class SlackPluginTest(TestCase):
    @fixture
    def plugin(self):
        return SlackPlugin()

    @responses.activate
    def test_simple_notification(self):
        responses.add('POST', 'http://example.com/slack')
        self.plugin.set_option('webhook', 'http://example.com/slack', self.project)

        group = self.create_group(message='Hello world', culprit='foo.bar')
        event = self.create_event(group=group, message='Hello world')

        rule = Rule.objects.create(project=self.project, label='my rule')

        notification = Notification(event=event, rule=rule)

        with self.options({'system.url-prefix': 'http://example.com'}):
            self.plugin.notify(notification)

        request = responses.calls[0].request
        payload = json.loads(parse_qs(request.body)['payload'][0])
        assert payload == {
            'parse': 'none',
            'username': 'Sentry',
            'attachments': [
                {
                    'color': '#f43f20',
                    'fields': [
                        {
                            'short': False,
                            'value': 'foo.bar',
                            'title': 'Culprit',
                        },
                        {
                            'short': True,
                            'value': 'foo Bar',
                            'title': 'Project'
                        },
                    ],
                    'fallback': '[foo Bar] Hello world',
                    'title': 'Hello world',
                    'title_link': 'http://example.com/baz/bar/issues/1/',
                },
            ],
        }

    @responses.activate
    def test_with_sorting(self):
        responses.add('POST', 'http://example.com/slack')
        self.plugin.set_option('webhook', 'http://example.com/slack', self.project)
        self.plugin.set_option('sort_on_tag', True, self.project)
        self.plugin.set_option('sort_on_tag_key', 'test_tag_key', self.project)
        self.plugin.set_option('group_1_tag_values', 'a,b,c', self.project)
        self.plugin.set_option('group_1_channel', '#test_channel', self.project)
        self.plugin.set_option('group_2_tag_values', 'd,e,f', self.project)
        self.plugin.set_option('group_3_tag_values', 'b', self.project)
        self.plugin.set_option('group_3_channel', '#test_channel2', self.project)

        group = self.create_group(message='Hello world', culprit='foo.bar')
        event = self.create_event(group=group, message='Hello world', tags={'test_tag_key': 'b'})

        rule = Rule.objects.create(project=self.project, label='my rule')

        notification = Notification(event=event, rule=rule)

        with self.options({'system.url-prefix': 'http://example.com'}):
            self.plugin.notify(notification)

        request = responses.calls[0].request
        payload = json.loads(parse_qs(request.body)['payload'][0])
        assert payload == {
            'channel': '#test_channel',
            'parse': 'none',
            'username': 'Sentry',
            'attachments': [
                {
                    'color': '#f43f20',
                    'fields': [
                        {
                            'short': False,
                            'value': 'foo.bar',
                            'title': 'Culprit',
                        },
                        {
                            'short': True,
                            'value': 'foo Bar',
                            'title': 'Project'
                        },
                    ],
                    'fallback': '[foo Bar] Hello world',
                    'title': 'Hello world',
                    'title_link': 'http://example.com/baz/bar/issues/1/',
                },
            ],
        }

        request = responses.calls[1].request
        payload = json.loads(parse_qs(request.body)['payload'][0])
        assert payload == {
            'channel': '#test_channel2',
            'parse': 'none',
            'username': 'Sentry',
            'attachments': [
                {
                    'color': '#f43f20',
                    'fields': [
                        {
                            'short': False,
                            'value': 'foo.bar',
                            'title': 'Culprit',
                        },
                        {
                            'short': True,
                            'value': 'foo Bar',
                            'title': 'Project'
                        },
                    ],
                    'fallback': '[foo Bar] Hello world',
                    'title': 'Hello world',
                    'title_link': 'http://example.com/baz/bar/issues/1/',
                },
            ],
        }
