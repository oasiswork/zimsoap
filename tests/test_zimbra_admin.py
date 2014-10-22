#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unittests against zimbraAdmin SOAP webservice

It has to be tested against a zimbra server (see properties.py) and is only
supposed to pass with the reference VMs.
"""

import unittest
import random

from zimsoap.client import *
from zimsoap.zobjects import *

from tests.properties import *

class ZimbraAdminClientTests(unittest.TestCase):
    def setUp(self):
        self.TEST_SERVER = TEST_HOST
        self.TEST_LOGIN = TEST_ADMIN_LOGIN
        self.TEST_PASSWORD = TEST_ADMIN_PASSWORD

    def testLogin(self):
        zc = ZimbraAdminClient(self.TEST_SERVER, TEST_ADMIN_PORT)
        zc.login(self.TEST_LOGIN, self.TEST_PASSWORD)
        self.assertTrue(zc._session.is_logged_in())

    def testBadLoginFailure(self):
        with self.assertRaises(ZimbraSoapServerError) as cm:
            zc = ZimbraAdminClient(self.TEST_SERVER, 7071)
            zc.login('badlogin@zimbratest.oasiswork.fr', self.TEST_PASSWORD)

        self.assertIn('authentication failed', cm.exception.http_msg)


    def testBadPasswordFailure(self):
        with self.assertRaises(ZimbraSoapServerError) as cm:
            zc = ZimbraAdminClient(self.TEST_SERVER, 7071)
            zc.login(self.TEST_LOGIN, 'badpassword')

        self.assertIn('authentication failed', cm.exception.http_msg)

    def testBadHostFailure(self):
        with self.assertRaises(urllib2.URLError) as cm:
            zc = ZimbraAdminClient('nonexistenthost.oasiswork.fr', 7071)
            zc.login(self.TEST_LOGIN, self.TEST_PASSWORD)

    def testBadPortFailure(self):
        with self.assertRaises(urllib2.URLError) as cm:
            zc = ZimbraAdminClient(self.TEST_SERVER, 9999)
            zc.login(self.TEST_LOGIN, self.TEST_PASSWORD)


class ZimbraAdminClientRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAdminClient(TEST_HOST, TEST_ADMIN_PORT)
        cls.zc.login(TEST_ADMIN_LOGIN, TEST_ADMIN_PASSWORD)


    def setUp(self):
        # self.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        # self.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

        self.EXISTANT_DOMAIN = TEST_DOMAIN1
        self.EXISTANT_MBOX_ID = "d78fd9c9-f000-440b-bce6-ea938d40fa2d"
        # Should not exist before the tests
        self.TEST_DL_NAME = 'unittest-test-list-1@%s' % self.EXISTANT_DOMAIN

    def tearDown(self):
        # Try to delete a relief test distribution list (if any)
        try:
            resp = self.zc.request('GetDistributionList', {
                    'dl': {'by': 'name', '_content': self.TEST_DL_NAME}
            })

            dl_id = resp['dl']['id']
            self.zc.request('DeleteDistributionList', {'id': dl_id})

        except ZimbraSoapServerError:
            pass

    def testGetAllAccountsReturnsSomething(self):
        resp = self.zc.request('GetAllAccounts')
        self.assertTrue(resp.has_key('account'), list)
        self.assertIsInstance(resp['account'], list)

    def testGetAlllCalendarResourcesReturnsSomething(self):
        resp = self.zc.request('GetAllCalendarResources')
        self.assertTrue(resp.has_key('calresource'), list)
        self.assertIsInstance(resp['calresource'], list)

    def testGetAllDomainsReturnsSomething(self):
        resp = self.zc.request('GetAllDomains')
        self.assertTrue(resp.has_key('domain'), list)
        self.assertIsInstance(resp['domain'], list)

    def testGetDomainReturnsDomain(self):
        resp = self.zc.request('GetDomain', {'domain' : {
                    'by': 'name',
                    '_content': self.EXISTANT_DOMAIN
        }})
        self.assertIsInstance(resp, dict)
        self.assertTrue(resp.has_key('domain'))
        self.assertIsInstance(resp['domain'], dict)

    def testGetMailboxStatsReturnsSomething(self):
        resp = self.zc.request('GetMailboxStats')
        self.assertTrue(resp.has_key('stats'))
        self.assertIsInstance(resp['stats'], dict)

    def testCountAccountReturnsSomething(self):
        """Count accounts on the first of domains"""
        first_domain_name = self.zc.get_all_domains()[0].name

        resp = self.zc.request_list(
            'CountAccount',
            {'domain': {'by': 'name', '_content': self.EXISTANT_DOMAIN}}
        )
        first_cos = resp[0]
        self.assertTrue(first_cos.has_key('id'))

        # will fail if not convertible to int
        self.assertIsInstance(int(first_cos['_content']), int)

    def testGetMailboxRequest(self):
        try:
            EXISTANT_MBOX_ID = self.testGetAllMailboxes()[0]['accountId']
        except e:
            raise e('failed in self.testGetAllMailboxes()')

        resp = self.zc.request('GetMailbox', {'mbox': {'id': EXISTANT_MBOX_ID}})
        self.assertIsInstance(resp['mbox'], dict)
        self.assertTrue(resp['mbox'].has_key('mbxid'))


    def testGetAllMailboxes(self):
        resp = self.zc.request('GetAllMailboxes')
        mailboxes = resp['mbox']
        self.assertIsInstance(resp['mbox'], list)
        return mailboxes

    def testCreateGetDeleteDistributionList(self):
        """ As Getting and deleting a list requires it to exist
        a list to exist, we group the 3 tests together.
        """

        def createDistributionList(name):
            resp = self.zc.request('CreateDistributionList', {'name': name})

            self.assertIsInstance(resp['dl'], dict)

        def getDistributionList(name):
            resp = self.zc.request('GetDistributionList',
                                   {'dl': {'by': 'name', '_content': name}})

            self.assertIsInstance(resp['dl'], dict)
            self.assertIsInstance(resp['dl']['id'], unicode)
            return resp['dl']['id']

        def deleteDistributionList(dl_id):
            resp = self.zc.request('DeleteDistributionList', {'id': dl_id})

        # Should not exist
        with self.assertRaises(ZimbraSoapServerError) as cm:
            getDistributionList(self.TEST_DL_NAME)

        createDistributionList(self.TEST_DL_NAME)

        # It should now exist
        list_id = getDistributionList(self.TEST_DL_NAME)

        deleteDistributionList(list_id)

        # Should no longer exists
        with self.assertRaises(ZimbraSoapServerError) as cm:
            getDistributionList(self.TEST_DL_NAME)


    def testCheckDomainMXRecord(self):

        domain = {'by': 'name', '_content': self.EXISTANT_DOMAIN}
        try:
            resp = self.zc.request('CheckDomainMXRecord', {'domain': domain})

        except ZimbraSoapServerError as sf:
            if not 'NameNotFoundException' in str(sf):
                # Accept for the moment this exception as it's kind a response
                # from server.
                raise

    def testGetAccount(self):
        account = {'by': 'name', '_content': TEST_LAMBDA_USER}
        resp = self.zc.request('GetAccount', {'account': account})
        self.assertIsInstance(resp['account'], dict)

    def testGetAccountInfo(self):
        account = {'by': 'name', '_content': TEST_LAMBDA_USER}
        resp = self.zc.request('GetAccountInfo', {'account': account})
        self.assertIsInstance(resp['cos']['id'], (str, unicode))


class PythonicAdminAPITests(unittest.TestCase):
    """ Tests the pythonic API, the one that should be accessed by someone using
    the library, zimbraAdmin features.
    """

    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAdminClient(TEST_HOST, TEST_ADMIN_PORT)
        cls.zc.login(TEST_ADMIN_LOGIN, TEST_ADMIN_PASSWORD)

    def setUp(self):
        # self.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        # self.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

        self.EXISTANT_DOMAIN = TEST_DOMAIN1
        self.EXISTANT_MBOX_ID = "d78fd9c9-f000-440b-bce6-ea938d40fa2d"
        # Should not exist before the tests
        self.TEST_DL_NAME = 'unittest-test-list-1@%s' % self.EXISTANT_DOMAIN

    def tearDown(self):
        try:
            self.zc.delete_distribution_list(
                DistributionList(name=self.TEST_DL_NAME))
        except (ZimbraSoapServerError, KeyError):
            pass

    def test_get_all_domains(self):
        doms = self.zc.get_all_domains()
        self.assertIsInstance(doms, list)
        self.assertIsInstance(doms[0], Domain)

        # Look for client1.unbound.oasiswork.fr
        found = False
        for i in doms:
            if i.name == self.EXISTANT_DOMAIN:
                found = True

        self.assertTrue(found)

    def test_get_domain(self):
        dom = self.zc.get_domain(Domain(name=TEST_DOMAIN1))
        self.assertIsInstance(dom, Domain)
        self.assertEqual(dom.name, TEST_DOMAIN1)

    def test_modify_domain(self):
        rand_str = random.randint(0,10**9)

        dom = self.zc.get_domain(Domain(name=TEST_DOMAIN1))
        a = {'zimbraAutoProvNotificationBody': rand_str}
        self.zc.modify_domain(dom, a)

        dom = self.zc.get_domain(Domain(name=TEST_DOMAIN1))
        self.assertEqual(dom['zimbraAutoProvNotificationBody'], rand_str)

    def test_get_all_accounts(self):
        accounts = self.zc.get_all_accounts()
        self.assertIsInstance(accounts[0], Account)
        self.assertEqual(len(accounts), 16)

    def test_get_all_accounts_by_single_server(self):
        test_server = Server(name='zimbratest.oasiswork.fr')
        accounts = self.zc.get_all_accounts(server=test_server)
        self.assertIsInstance(accounts[0], Account)
        self.assertEqual(len(accounts), 16)

    def test_get_all_accounts_by_single_domain(self):
        test_domain = Domain(name=TEST_DOMAIN2)
        accounts = self.zc.get_all_accounts(domain=test_domain)
        self.assertIsInstance(accounts[0], Account)
        self.assertEqual(len(accounts), 5)

    def test_get_all_accounts_by_single_domain_and_server(self):
        test_domain = Domain(name=TEST_DOMAIN2)
        test_server = Server(name='zimbratest.oasiswork.fr')
        accounts = self.zc.get_all_accounts(domain=test_domain,
                                            server=test_server)
        self.assertIsInstance(accounts[0], Account)
        self.assertEqual(len(accounts), 5)

    def test_get_all_accounts_exclusion_filters(self):
        # The TEST_DOMAIN1 contains 5 user accounts, 1 system and 1 admin
        test_domain = Domain(name=TEST_DOMAIN1)

        accounts = self.zc.get_all_accounts(
            domain=test_domain,
            include_system_accounts=True, include_admin_accounts=True)
        self.assertEqual(len(accounts), 10)

        accounts_no_admin = self.zc.get_all_accounts(
            domain=test_domain,
            include_system_accounts=True, include_admin_accounts=False)
        self.assertEqual(len(accounts_no_admin), 9)

        accounts_no_system = self.zc.get_all_accounts(
            domain=test_domain,
            include_system_accounts=False, include_admin_accounts=True)
        self.assertEqual(len(accounts_no_system), 6)

        accounts_no_admin_no_system = self.zc.get_all_accounts(
            domain=test_domain,
            include_admin_accounts=False, include_system_accounts=False)
        self.assertEqual(len(accounts_no_admin_no_system), 5)

    def test_get_all_calendar_resources(self):
        resources = self.zc.get_all_calendar_resources()
        self.assertIsInstance(resources[0], CalendarResource)
        self.assertEqual(len(resources), 2)

    def test_get_all_calendar_resources_by_single_server(self):
        test_server = Server(name='zimbratest.oasiswork.fr')
        resources = self.zc.get_all_calendar_resources(server=test_server)
        self.assertIsInstance(resources[0], CalendarResource)
        self.assertEqual(len(resources), 2)

    def test_get_all_calendar_resources_by_single_domain(self):
        test_domain = Domain(name=TEST_DOMAIN2)
        resources = self.zc.get_all_calendar_resources(domain=test_domain)
        self.assertEqual(len(resources), 1)

    def test_get_calendar_resource(self):
        calendar_resource = self.zc.get_calendar_resource(
            CalendarResource(name=TEST_CALRES1))
        self.assertIsInstance(calendar_resource, CalendarResource)
        self.assertEqual(calendar_resource.name, TEST_CALRES1)

        # Now grab it by ID
        calendar_resource_by_id = self.zc.get_calendar_resource(
            CalendarResource(id=calendar_resource.id))
        self.assertIsInstance(calendar_resource_by_id, CalendarResource)
        self.assertEqual(calendar_resource_by_id.name, TEST_CALRES1)
        self.assertEqual(calendar_resource_by_id.id, calendar_resource.id)


    def test_create_get_update_delete_calendar_resource(self):
        name = 'test-{}@zimbratest.oasiswork.fr'.format(
            random.randint(0,10**9))
        res_req = CalendarResource(name=name)

        with self.assertRaises(ZimbraSoapServerError) as cm:
            print self.zc.get_calendar_resource(res_req)

        # CREATE
        res = self.zc.create_calendar_resource(name, 'password', {
            'displayName'     : 'test display name',
            'zimbraCalResType': CalendarResource.EQUIPMENT_TYPE
        })

        self.assertIsInstance(res, CalendarResource)
        self.assertEqual(res.name, name)

        # GET
        res_got = self.zc.get_calendar_resource(res_req)
        self.assertIsInstance(res_got, CalendarResource)
        self.assertEqual(res.name, name)

        # UPDATE
        random_name_1 =  'test-{}'.format(random.randint(0,10**9))
        self.zc.modify_calendar_resource(res_got, {'displayName': random_name_1})

        res_got = self.zc.get_calendar_resource(res_req)
        self.assertEqual(res_got['displayName'], random_name_1)

        # DELETE
        self.zc.delete_calendar_resource(res_got)

        with self.assertRaises(ZimbraSoapServerError) as cm:
            self.zc.get_calendar_resource(res)


    def test_get_mailbox_stats(self):
        stats = self.zc.get_mailbox_stats()
        self.assertIsInstance(stats, dict)
        self.assertIsInstance(stats['numMboxes'], int)
        self.assertIsInstance(stats['totalSize'], int)

    def test_count_account(self):
        d = Domain(name=self.EXISTANT_DOMAIN)

        # ex return: list: ((<ClassOfService object>, <int>), ...)
        cos_counts = self.zc.count_account(d)

        self.assertIsInstance(cos_counts, list)
        self.assertIsInstance(cos_counts[0], tuple)
        self.assertIsInstance(cos_counts[0][0], ClassOfService)
        self.assertIsInstance(cos_counts[0][1], int)

    def test_get_all_mailboxes(self):
        mboxes = self.zc.get_all_mailboxes()
        self.assertIsInstance(mboxes, list)
        self.assertIsInstance(mboxes[0], Mailbox)

    def test_account_mailbox(self):
        # First, fetch an existing account_id
        first_account_id = self.zc.get_all_mailboxes()[0].accountId

        mbox = self.zc.get_account_mailbox(first_account_id)
        self.assertTrue(hasattr(mbox, 'mbxid'))
        self.assertTrue(hasattr(mbox, 's')) # size


    def test_create_get_delete_distribution_list(self):
        name = self.TEST_DL_NAME
        dl_req = DistributionList(name=name)

        with self.assertRaises(ZimbraSoapServerError) as cm:
            print self.zc.get_distribution_list(dl_req)

        dl = self.zc.create_distribution_list(name)
        self.assertIsInstance(dl, DistributionList)
        self.assertEqual(dl.name, name)

        dl_list = self.zc.get_all_distribution_lists()
        self.assertIsInstance(dl_list[0], DistributionList)

        dl_got = self.zc.get_distribution_list(dl_req)
        self.assertIsInstance(dl_got, DistributionList)
        self.assertEqual(dl_got, dl_list[0])

        self.zc.delete_distribution_list(dl_got)

        with self.assertRaises(ZimbraSoapServerError) as cm:
            self.zc.get_distribution_list(dl)

    def test_delete_distribution_list_by_name(self):
        name = self.TEST_DL_NAME
        dl_req = DistributionList(name=name)
        dl_full = self.zc.create_distribution_list(name)
        self.zc.delete_distribution_list(dl_req)

        # List with such a name does not exist
        with self.assertRaises(ZimbraSoapServerError) as cm:
            self.zc.get_distribution_list(dl_req)

        # List with such an ID does not exist
        with self.assertRaises(ZimbraSoapServerError) as cm:
            self.zc.get_distribution_list(dl_full)

    def test_get_account(self):
        account = self.zc.get_account(Account(name=TEST_LAMBDA_USER))
        self.assertIsInstance(account, Account)
        self.assertEqual(account.name, TEST_LAMBDA_USER)

        # Now grab it by ID
        account_by_id = self.zc.get_account(Account(id=account.id))
        self.assertIsInstance(account_by_id, Account)
        self.assertEqual(account_by_id.name, TEST_LAMBDA_USER)
        self.assertEqual(account_by_id.id, account.id)

    def test_get_account_cos(self):
        cos = self.zc.get_account_cos(Account(name=TEST_LAMBDA_USER))
        self.assertIsInstance(cos, COS)
        self.assertEqual(cos.name, 'default')
        self.assertRegexpMatches(cos.id, r'[\w\-]{36}')

    def test_mk_auth_token_succeeds(self):
        user = Account(name='admin@{0}'.format(TEST_DOMAIN1))
        tk = self.zc.mk_auth_token(user, 0)
        self.assertIsInstance(tk, str)

    def test_mk_auth_token_fails_if_no_key(self):
        user = Account(name='admin@{0}'.format(TEST_DOMAIN2))

        with self.assertRaises(DomainHasNoPreAuthKey) as cm:
            self.zc.mk_auth_token(user, 0)

    def test_admin_get_logged_in_by(self):
        new_zc = ZimbraAdminClient(TEST_HOST, TEST_ADMIN_PORT)
        new_zc.get_logged_in_by(TEST_ADMIN_LOGIN, self.zc)
        self.assertTrue(new_zc._session.is_logged_in())
        self.assertTrue(new_zc._session.is_session_valid())

    def test_admin_delegate_auth(self):
        zc_account = self.zc.delegate_auth(Account(name=TEST_LAMBDA_USER))
        self.assertTrue(zc_account._session.is_logged_in())
        self.assertTrue(zc_account._session.is_session_valid())

    def test_admin_get_account_authToken1(self):
        """ From an existing account """
        authToken, lifetime = self.zc.get_account_authToken(
            account=Account(name=TEST_LAMBDA_USER)
        )
        new_zc = ZimbraAccountClient(TEST_HOST)
        new_zc.login_with_authToken(authToken, lifetime)
        self.assertTrue(new_zc._session.is_logged_in())
        self.assertTrue(new_zc._session.is_session_valid())

    def test_admin_get_account_authToken2(self):
        """ From an account name """
        authToken, lifetime = self.zc.get_account_authToken(
            account_name=TEST_LAMBDA_USER
        )
        new_zc = ZimbraAccountClient(TEST_HOST)
        new_zc.login_with_authToken(authToken, lifetime)
        self.assertTrue(new_zc._session.is_logged_in())
        self.assertTrue(new_zc._session.is_session_valid())


class ZimbraAPISessionTests(unittest.TestCase):
    def setUp(self):
        self.cli = ZimbraAdminClient(TEST_HOST, TEST_ADMIN_PORT)
        self.session = ZimbraAPISession(self.cli)

    def testInit(self):
        self.session = ZimbraAPISession(self.cli)
        self.assertFalse(self.session.is_logged_in())

    def testSuccessfullLogin(self):
        self.session.login(TEST_ADMIN_LOGIN, TEST_ADMIN_PASSWORD)

        self.assertTrue(self.session.is_logged_in())

    def testGoodSessionValidates(self):
        self.session.login(TEST_ADMIN_LOGIN, TEST_ADMIN_PASSWORD)
        self.assertTrue(self.session.is_session_valid())

    def testBadSessionFails(self):
        self.session.login(TEST_ADMIN_LOGIN, TEST_ADMIN_PASSWORD)
        self.session.authToken = '42'
        self.assertFalse(self.session.is_session_valid())

