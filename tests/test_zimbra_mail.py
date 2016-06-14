#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Integration tests against zimbraMail SOAP webservice

It has to be tested against a zimbra server (see README.md).
"""

import unittest
import random

from zimsoap.client import (ZimbraMailClient, ZimbraAdminClient,
                            ZimbraSoapServerError)
from zimsoap.zobjects import Task, Contact, Account
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
        self.contact_id = None

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

    def test_grant_get_revoke_permission(self):
        admin_zc = ZimbraAdminClient(
            TEST_CONF['host'], TEST_CONF['admin_port']
        )
        admin_zc.login(TEST_CONF['admin_login'], TEST_CONF['admin_password'])

        right = 'sendAs'

        self.zc.grant_permission(
            right=right,
            grantee_name=TEST_CONF['lambda_user2']
        )

        perm = self.zc.get_permission(right)
        self.assertTrue(perm['ace']['d'], TEST_CONF['lambda_user2'])

        self.zc.revoke_permission(
            right=right,
            grantee_name=TEST_CONF['lambda_user2']
        )
        perm = self.zc.get_permission(right)
        self.assertEqual(perm, {})

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

    # Raking actions

    def test_delete_ranking(self):
        # No means to check it's really deleted because we
        # can't access the list and no error is thrown if
        # there is no entry with this address.
        self.zc.delete_ranking(email='p.martin@example.com')

    def test_reset_ranking(self):
        # Same as above, no means to check it's really reseted.
        self.zc.reset_ranking()

    # Contact

    def test_create_get_delete_contact(self):
        random_address = 'email' + str(random.randint(0, 10**9))

        # CREATE
        attrs = {'firstName': 'Pierre',
                 'lastName': 'MARTIN',
                 'email': random_address}
        contact = self.zc.create_contact(attrs=attrs)

        self.assertIsInstance(contact, Contact)
        self.assertEqual(contact._a_tags.get('email'), random_address)

        # GET
        contacts = self.zc.get_contacts(ids=contact.id)
        self.assertIsInstance(contacts[0], Contact)

        # UPDATE (TO DO)

        # DELETE
        self.zc.delete_contacts([contact.id])
        with self.assertRaises(ZimbraSoapServerError):
            self.zc.get_contacts(ids=contact.id)

    def test_create_delete_group(self):
        random_address = 'email' + str(random.randint(0, 10**9))
        group_name = 'group_test'

        # CREATE

        # create a contact to add into the group
        contact_attrs = {
            'firstName': 'Pierre',
            'lastName': 'MARTIN',
            'email': random_address
        }
        contact = self.zc.create_contact(attrs=contact_attrs)

        members = [
            {'type': 'C', 'value': contact.id},
            {'type': 'I', 'value': 'manual_addresse@example.com'},
            {'type': 'G',
             'value': 'uid=albacore,ou=people,dc=zimbratest,dc=example,dc=com'}
        ]

        group_attrs = {
            'nickname': group_name,
            'type': 'group'
        }

        group = self.zc.create_group(attrs=group_attrs, members=members)

        self.assertIsInstance(group, Contact)
        self.assertEqual(group['nickname'], group_name)

        # UPDATE (TO DO)

        # DELETE
        self.zc.delete_contacts([group.id])
        with self.assertRaises(ZimbraSoapServerError):
            self.zc.get_contacts(ids=group.id)
        self.zc.delete_contacts([contact.id])

    # Conversation

    def test_get_move_delete_conversation(self):
        # Adding a message to create a conversation
        with open('tests/data/email.msg') as f:
            message_content = f.read()
            msg = self.zc.add_message(
                message_content,
                folder="/Inbox",
                d='1451579153000'
            )

        conv_id = msg['m']['cid']
        # GET
        conv = self.zc.get_conversation(conv_id)
        self.assertEqual(abs(int(conv['c']['m']['id'])), abs(int(conv_id)))

        # MOVE
        self.zc.move_conversations(conv_id.split(), 3)
        conv = self.zc.get_conversation(conv_id)
        self.assertEqual(conv['c']['m']['l'], '3')

        # DELETE
        self.zc.delete_conversations(conv_id.split())
        with self.assertRaises(ZimbraSoapServerError):
            self.zc.get_conversation(conv_id)

    # Data source_addresses

    def test_add_get_update_delete_datasource(self):
        # ADD
        source_dic = {
            'imap': {
                'connectionType': 'tls',
                'emailAddress': 'external@domain.com',
                'host': 'mail.domain.com',
                'importOnly': '1',
                'isEnabled': '0',
                'leaveOnServer': '0',
                'name': 'My IMAP account',
                'password': 'data-source-password',
                'port': '993',
                'replyToDisplay': 'An Other Name',
                'useAddressForForwardReply': '0',
                'username': 'data-source-username'
            }
        }
        created_source = self.zc.create_data_source(source_dic, 'MyImapDir')
        self.assertTrue(created_source)

        # GET
        source_id = created_source['imap']['id']
        # get by id
        get_source_by_id = self.zc.get_data_sources(source_id=source_id)
        self.assertEqual(get_source_by_id['imap'][0]['emailAddress'],
                         source_dic['imap']['emailAddress'])

        # get by source address
        get_source_by_address = self.zc.get_data_sources(
            source_addresses=[source_dic['imap']['emailAddress']])
        self.assertEqual(get_source_by_address['imap'][0]['emailAddress'],
                         source_dic['imap']['emailAddress'])

        # get by types
        get_source_by_types = self.zc.get_data_sources(types=['imap'])
        self.assertEqual(get_source_by_types['imap'][0]['emailAddress'],
                         source_dic['imap']['emailAddress'])

        # get by non present types
        get_source_by_ntypes = self.zc.get_data_sources(types=['pop3'])
        self.assertFalse(get_source_by_ntypes['pop3'])

        # UPDATE
        new_address = 'modified_external@domain.com'
        created_source['imap']['emailAddress'] = new_address
        self.zc.modify_data_source(created_source)
        updated_source = self.zc.get_data_sources(source_id=source_id)
        self.assertEqual(updated_source['imap'][0]['emailAddress'],
                         new_address)

        # DELETE
        self.zc.delete_data_source(created_source)
        self.assertFalse(
            self.zc.get_data_sources(source_id=created_source['imap']['id']))

    # Message

    def test_add_get_update_delete_message(self):
        # ADD
        with open('tests/data/email.msg') as f:
            message_content = f.read()
            msg = self.zc.add_message(
                message_content,
                folder="/Inbox",
                d='1451579153000'
            )

        self.assertEqual(msg['m']['d'], '1451579153000')

        # GET
        msg_id = msg['m']['id']
        msg_get = self.zc.get_message(msg_id)

        self.assertEqual(msg_id, msg_get['m']['id'])

        # MOVE
        self.zc.move_messages([msg_id], '3')

        self.zc.update_messages_flag([msg_id], 'f')
        msg_get_after_mod = self.zc.get_message(msg_id)

        self.assertEqual(msg_get_after_mod['m']['l'], '3')
        self.assertEqual(msg_get_after_mod['m']['f'], 'f')

        # DELETE
        self.zc.delete_messages(msg['m']['id'].split())

        with self.assertRaises(ZimbraSoapServerError):
            self.zc.get_message(msg['m']['id'])

    # Folder

    def test_create_delete_folder(self):
        folder_name = 'TestingFolder'
        folder = self.zc.create_folder(folder_name)
        new_folder = self.zc.get_folder(f_id=folder['id'])['folder']
        self.assertEqual(folder_name, new_folder['name'])

        self.zc.delete_folder([new_folder['id']])
        with self.assertRaises(ZimbraSoapServerError):
            self.zc.get_folder(f_id=new_folder['id'])

    def test_get_folder(self):
        folder = self.zc.get_folder(path="/Inbox")
        self.assertEqual(folder['folder']['id'], '2')

    def test_folder_grant_mount_revoke(self):
        admin_zc = ZimbraAdminClient(TEST_CONF['host'],
                                     TEST_CONF['admin_port'])
        admin_zc.login(TEST_CONF['admin_login'], TEST_CONF['admin_password'])

        grantee_zc = ZimbraMailClient(TEST_CONF['host'])
        grantee_zc.delegated_login(TEST_CONF['lambda_user2'], admin_zc)

        grantee_id = admin_zc.get_account(
            Account(name=TEST_CONF['lambda_user2'])
        )._a_tags['zimbraId']

        right = 'rwidx'
        self.zc.modify_folder_grant(
            folder_ids=['1'],
            perm=right,
            zid=grantee_id
        )

        f_gt = self.zc.get_folder_grant(path='/')
        self.assertEqual(f_gt['grant']['perm'], right)
        self.assertEqual(f_gt['grant']['d'], TEST_CONF['lambda_user2'])

        mount_name = 'MountedZimsoapTest'
        grantee_zc.create_mountpoint(
            name=mount_name,
            path='/',
            owner=TEST_CONF['lambda_user'],
            parent_id='1'
        )
        mount_path = '/' + mount_name
        link = grantee_zc.get_folder(path=mount_path)['link']
        self.assertEqual(link['name'], mount_name)
        self.assertEqual(link['owner'], TEST_CONF['lambda_user'])

        # Clean grantee
        grantee_zc.delete_folder([link['id']])

        # Revoke rights
        self.zc.modify_folder_grant(
            folder_ids=['1'],
            perm='none',
            zid=grantee_id
        )
        f_gt = self.zc.get_folder_grant(path='/')
        self.assertEqual(f_gt, {})

    # Search

    def test_search(self):
        with open('tests/data/email.msg') as f:
            message_content = f.read()
            msg = self.zc.add_message(
                message_content,
                folder="/Inbox",
                d='1451579153000'
            )
        msg_req = self.zc.search(query="in:/Inbox date:12/31/15")

        # Clean
        self.zc.delete_messages(msg['m']['id'].split())

        self.assertEqual(msg['m']['id'], msg_req['c']['m']['id'])


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
