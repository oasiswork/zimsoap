#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Integration tests against zimbraMail SOAP webservice

It has to be tested against a zimbra server (see README.md).
"""

import unittest

from zimsoap.client import ZimbraMailClient, ZimbraAdminClient
from zimsoap.zobjects import Task
from zimsoap import utils
import tests

TEST_CONF = tests.get_config()


class ZimbraMailAPITests(unittest.TestCase):
    """ Test logic and Zimbra Mail SOAP methods """

    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraMailClient(TEST_CONF['host'])
        cls.zc.login(TEST_CONF['lambda_user'], TEST_CONF['lambda_password'])

    def setUp(self):
        self.TEST_SERVER = TEST_CONF['host']
        self.TEST_LOGIN = TEST_CONF['lambda_user']
        self.TEST_PASSWORD = TEST_CONF['lambda_password']
        self.task_id = None

    """
    def tearDown(self):
        # Delete the test task (if any)
        We should use here CancelTaskRequest ?
    """

    def test_CreateTaskRequest(self):
        xml = """
            <m su="{subject}">
                <inv>
                    <comp percentComplete="0" name="{subject}">
                        <fr>{desc}</fr>
                        <desc>{desc}</desc>
                    </comp>
                </inv>
                <mp>
                    <content></content>
                </mp>
            </m>
        """.format(
            subject='test_CreateTaskRequest',
            desc='Task Content'
        )
        task = utils.xml_str_to_dict(xml)
        resp = self.zc.request('CreateTask', task)

        # store created task id
        self.task_id = resp['calItemId']

    def test_GetTaskRequest(self):
        xml = """
            <m su="{subject}">
                <inv>
                    <comp percentComplete="0" name="{subject}">
                        <fr>{desc}</fr>
                        <desc>{desc}</desc>
                    </comp>
                </inv>
                <mp>
                    <content></content>
                </mp>
            </m>
        """.format(
            subject='test_GetTaskRequest',
            desc='Task Content'
        )

        task = utils.xml_str_to_dict(xml)
        resp = self.zc.request('CreateTask', task)

        # store created task id
        self.task_id = resp['calItemId']

        resp = self.zc.request('GetTask', {'id': self.task_id})

        # Just checks success (check on response tag is in request())


class PythonicZimbraMailAPITests(unittest.TestCase):
    """ Tests the pythonic API, the one that should be accessed by someone
    using the library, zimbraMail features.
    """

    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraMailClient(TEST_CONF['host'])
        cls.zc.login(TEST_CONF['lambda_user'], TEST_CONF['lambda_password'])

    def setUp(self):
        self.TEST_SERVER = TEST_CONF['host']
        self.TEST_LOGIN = TEST_CONF['lambda_user']
        self.TEST_PASSWORD = TEST_CONF['lambda_password']
        self.task_id = None

    """
    def tearDown(self):
        # Delete the test task (if any)
        We should use here CancelTaskRequest ?
    """

    def test_login(self):
        zc = ZimbraMailClient(self.TEST_SERVER)
        zc.login(self.TEST_LOGIN, self.TEST_PASSWORD)
        self.assertTrue(zc._session.is_logged_in())

    def test_create_task(self):
        subject = 'test_create_task'
        desc = 'Task Content'
        task_id = self.zc.create_task(subject, desc)
        # store created task id
        self.task_id = task_id

        self.assertNotEqual(task_id, None)

    def test_get_task(self):
        subject = 'test_get_task'
        desc = 'Task Content'
        task_id = self.zc.create_task(subject, desc)
        # store created task id
        self.task_id = task_id

        task = self.zc.get_task(task_id)
        self.assertIsInstance(task, Task)
        self.assertEqual(task.id, task_id)

    def test_account_delegated_login(self):
        admin_zc = ZimbraAdminClient(TEST_CONF['host'],
                                     TEST_CONF['admin_port'])
        admin_zc.login(TEST_CONF['admin_login'], TEST_CONF['admin_password'])

        new_zc = ZimbraMailClient(TEST_CONF['host'])
        new_zc.delegated_login(TEST_CONF['lambda_user'], admin_zc)

        self.assertTrue(new_zc._session.is_logged_in())
        self.assertTrue(new_zc.is_session_valid())


class ZobjectTaskTests(unittest.TestCase):
    """ Tests the Task zobject.
    """

    def test_to_creator(self):
        task = Task()
        subject = 'Task Subject'
        desc = 'Task Content'

        req = task.to_creator(subject, desc)
        self.assertEqual(req['m']['su'], subject)
        self.assertEqual(req['m']['inv']['comp']['fr']['_content'], desc)
        self.assertEqual(req['m']['inv']['comp']['desc']['_content'], desc)
