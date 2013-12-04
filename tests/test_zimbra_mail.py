#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
# Unit tests, using unittest module, bundled with python. It has to be tested
# against a Zimbra server.
#

import unittest

from zimsoap.client import ZimbraMailClient
from zimsoap.zobjects import Task
from zimsoap import utils

TEST_HOST = '192.168.33.10'
TEST_ADMIN_PORT = '7071'

TEST_DOMAIN = 'zimbratest.oasiswork.fr'

TEST_ADMIN_LOGIN = 'admin@' + TEST_DOMAIN
TEST_ADMIN_PASSWORD = 'password'

TEST_LAMBDA_USER = 'albacore@' + TEST_DOMAIN
TEST_LAMBDA_PASSWORD = 'albacore'


class ZimbraMailAPITests(unittest.TestCase):
    """ Test logic and Zimbra Mail SOAP methods """

    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraMailClient(TEST_HOST)
        cls.zc.login(TEST_LAMBDA_USER, TEST_LAMBDA_PASSWORD)

    def setUp(self):
        self.TEST_SERVER = TEST_HOST
        self.TEST_LOGIN = TEST_LAMBDA_USER
        self.TEST_PASSWORD = TEST_LAMBDA_PASSWORD
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
        cls.zc = ZimbraMailClient(TEST_HOST)
        cls.zc.login(TEST_LAMBDA_USER, TEST_LAMBDA_PASSWORD)

    def setUp(self):
        self.TEST_SERVER = TEST_HOST
        self.TEST_LOGIN = TEST_LAMBDA_USER
        self.TEST_PASSWORD = TEST_LAMBDA_PASSWORD
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
