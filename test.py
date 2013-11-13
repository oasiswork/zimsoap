#!/usr/bin/env python
#
# Unit tests, using unittest module, bundled with python. It has to be tested
# against a Zimbra server.
#

import unittest
import urllib2
from os.path import dirname, abspath, join


import pysimplesoap
from pysimplesoap.client import SimpleXMLElement

import zimsoap.utils
from tests import samples
from zimsoap.client import *
from zimsoap.zobjects import *

TEST_HOST="192.168.33.10"
TEST_ADMIN_PORT="7071"

TEST_DOMAIN1="zimbratest.oasiswork.fr"
TEST_DOMAIN2="zimbratest2.oasiswork.fr"
TEST_DOMAIN13="zimbratest3.oasiswork.fr"

TEST_ADMIN_LOGIN="admin@"+TEST_DOMAIN1
TEST_ADMIN_PASSWORD="password"

TEST_LAMBDA_USER="albacore@"+TEST_DOMAIN1
TEST_LAMBDA_PASSWORD="albacore"

class ZimbraAPISessionTests(unittest.TestCase):
    def setUp(self):
        self.loc = "https://%s:%s/service/admin/soap" % (TEST_HOST, TEST_ADMIN_PORT)
        self.cli = pysimplesoap.client.SoapClient(
            location=self.loc, action=self.loc,
            namespace='urn:zimbraAdmin', ns=False)
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

    def testHeader(self):
        self.session.login(TEST_ADMIN_LOGIN, TEST_ADMIN_PASSWORD)
        self.session.get_context_header()

    def testHeaderNotLogged(self):
        with self.assertRaises(ShouldAuthenticateFirst) as cm:
            self.session.get_context_header()


class ZimbraAccountClientTests(unittest.TestCase):
    """ Is pretty uncomplete as it's testing code common to admin, see class after this one.
    """
    def setUp(self):
        self.TEST_SERVER = TEST_HOST
        self.TEST_LOGIN = TEST_LAMBDA_USER
        self.TEST_PASSWORD = TEST_LAMBDA_PASSWORD

    def testLogin(self):
        zc = ZimbraAccountClient(self.TEST_SERVER)
        zc.login(self.TEST_LOGIN, self.TEST_PASSWORD)
        self.assertTrue(zc._session.is_logged_in())

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
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            zc = ZimbraAdminClient(self.TEST_SERVER, 7071)
            zc.login('badlogin@zimbratest.oasiswork.fr', self.TEST_PASSWORD)

        self.assertEqual(cm.exception.faultcode, 'soap:Client')

    def testBadPasswordFailure(self):
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            zc = ZimbraAdminClient(self.TEST_SERVER, 7071)
            zc.login(self.TEST_LOGIN, 'badpassword')

        self.assertEqual(cm.exception.faultcode, 'soap:Client')

    def testBadHostFailure(self):
        with self.assertRaises(urllib2.URLError) as cm:
            zc = ZimbraAdminClient('nonexistenthost.oasiswork.fr', 7071)
            zc.login(self.TEST_LOGIN, self.TEST_PASSWORD)

    def testBadPortFailure(self):
        with self.assertRaises(urllib2.URLError) as cm:
            zc = ZimbraAdminClient(self.TEST_SERVER, 9999)
            zc.login(self.TEST_LOGIN, self.TEST_PASSWORD)


class ZimbraAccountClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAccountClient(TEST_HOST)
        cls.zc.login(TEST_LAMBDA_USER, TEST_LAMBDA_PASSWORD)

    def testGetSignaturesReturnsSomething(self):
        resp = self.zc.GetSignaturesRequest()
        resp_tag = utils.extractResponseTag(resp)
        self.assertEqual(resp_tag.get_name(), 'GetSignaturesResponse')


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
            xml_node = SimpleXMLElement(
                '<l><dl by="name" >%s</dl></l>' % self.TEST_DL_NAME)
            resp = self.zc.GetDistributionListRequest(self.zc, xml_node)
            xml_dl_id = zimsoap.utils.extractSingleResponse(resp)['id']
            self.zc.DeleteDistributionListRequest(
                attributes={'id': dl_id})

        except pysimplesoap.client.SoapFault:
            pass

    def testGetAllAccountsReturnsSomething(self):
        resp = self.zc.GetAllAccountsRequest()
        self.assertIsInstance(resp, SimpleXMLElement)

    def testGetAllAccountsReturnsSomething(self):
        resp = self.zc.GetAllAccountsRequest()
        self.assertIsInstance(resp, SimpleXMLElement)

    def testGetAllDomainsReturnsSomething(self):
        resp = self.zc.GetAllDomainsRequest()
        self.assertIsInstance(resp, SimpleXMLElement)

    def testGetAllDomainsReturnsDomains(self):
        resp = zimsoap.utils.extractResponses(self.zc.GetAllDomainsRequest())
        for tag in resp:
            self.assertEqual(tag.get_name(), 'domain')

    def testGetDomainReturnsDomain(self):
        xml_node = SimpleXMLElement(
            '<l><domain by="name">{}</domain></l>'.format(
                self.EXISTANT_DOMAIN))
        resp = zimsoap.utils.extractSingleResponse(
            self.zc.GetDomainRequest(self.zc,xml_node)
            )
        self.assertIsInstance(resp, SimpleXMLElement)
        self.assertEqual(resp.get_name(), 'domain')

    def testGetMailboxStatsReturnsSomething(self):
        resp = self.zc.GetMailboxStatsRequest()
        self.assertIsInstance(resp, SimpleXMLElement)

    def testCountAccountReturnsSomething(self):
        """Count accounts on the first of domains"""
        first_domain_name = self.zc.get_all_domains()[0].name

        # FIXME: the <l> is a total workarround
        xml_node = SimpleXMLElement(
            '<l><domain by="name">%s</domain></l>' % self.EXISTANT_DOMAIN)
        resp = self.zc.CountAccountRequest(self.zc,xml_node)
        first_cos = zimsoap.utils.extractResponses(resp)[0]
        self.assertEqual(first_cos.get_name(), 'cos')
        self.assertTrue(first_cos.attributes().has_key('id'))

        # will fail if not convertible to int
        self.assertIsInstance(int(first_cos), int)

    def testGetMailboxRequest(self):
        try:
            EXISTANT_MBOX_ID = self.testGetAllMailboxes()[0]['accountId']
        except e:
            raise e('failed in self.testGetAllMailboxes()')

        xml_node = SimpleXMLElement(
            '<l><mbox id="%s" /></l>' % EXISTANT_MBOX_ID)

        resp = self.zc.GetMailboxRequest(self.zc, xml_node)
        first_mbox = zimsoap.utils.extractResponses(resp)[0]
        self.assertEqual(first_mbox.get_name(), 'mbox')
        self.assertTrue(first_mbox.attributes().has_key('mbxid'))


    def testGetAllMailboxes(self):
        resp = self.zc.GetAllMailboxesRequest()
        mailboxes = zimsoap.utils.extractResponses(resp)
        self.assertEqual(mailboxes[0].get_name(), 'mbox')
        return mailboxes

    def testCreateGetDeleteDistributionList(self):
        """ As Getting and deleting a list requires it to exist
        a list to exist, we group the 3 tests together.
        """

        def createDistributionList(name):
            resp = self.zc.CreateDistributionListRequest(
                attributes={'name': name})
            dls = zimsoap.utils.extractSingleResponse(resp)
            self.assertEqual(dls.get_name(), 'dl')

        def getDistributionList(name):
            xml_node = SimpleXMLElement(
                '<l><dl by="name" >%s</dl></l>' % name)

            resp = self.zc.GetDistributionListRequest(self.zc, xml_node)
            xml_dl = zimsoap.utils.extractSingleResponse(resp)
            self.assertEqual(xml_dl.get_name(), 'dl')
            self.assertIsInstance(xml_dl['id'], unicode)
            return xml_dl['id']

        def deleteDistributionList(dl_id):
            resp = self.zc.DeleteDistributionListRequest(
                attributes={'id': dl_id})

        # Should not exist
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            getDistributionList(self.TEST_DL_NAME)

        createDistributionList(self.TEST_DL_NAME)

        # It should now exist
        list_id = getDistributionList(self.TEST_DL_NAME)

        deleteDistributionList(list_id)

        # Should no longer exists
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            getDistributionList(self.TEST_DL_NAME)


    def testCheckDomainMXRecord(self):
        xml_node = SimpleXMLElement(
            '<l><domain by="name">%s</domain></l>' % self.EXISTANT_DOMAIN)

        try:
            resp = self.zc.CheckDomainMXRecordRequest(self.zc, xml_node)
        except pysimplesoap.client.SoapFault as sf:
            if not 'NameNotFoundException' in str(sf):
                # Accept for the moment this exception as it's kind a response
                # from server.
                raise

        # xml = zimsoap.utils.extractResponses(resp)
        # self.assertEqual(xml_dl[0].get_name(), 'entry')
        # self.assertEqual(xml_dl[0].get_name(), 'code')
        # self.assertEqual(xml_dl[0].get_name(), 'message')


class ZObjectsTests(unittest.TestCase):
    def setUp(self):
        self.simple_domain = SimpleXMLElement(samples.SIMPLE_DOMAIN)
        self.misnamed_domain = SimpleXMLElement(samples.MISNAMED_DOMAIN)
        self.mbox = SimpleXMLElement(samples.MBOX)

    def testDomainFromXML(self):
        d = Domain.from_xml(self.simple_domain)
        self.assertIsInstance(d, Domain)
        self.assertIsInstance(d.id, str)
        self.assertIsInstance(d.name, str)
        self.assertIsNotNone(d.id)
        self.assertEqual(d.name, 'client1.unbound.oasiswork.fr')

    def testDomainWithWrongTagNameFails(self):
        with self.assertRaises(TypeError) as cm:
            d = Domain.from_xml(self.misnamed_domain)

    def testDomainSelector(self):
        d = Domain(name='foo')
        s = d.to_xml_selector()
        s.get_name() == 'domain'
        self.assertEqual(s['by'], 'name')
        self.assertEqual(str(s), 'foo')

    def testInvalidDomainSelector(self):
        with self.assertRaises(ValueError) as cm:
            Domain().to_xml_selector()

        # Should not produce a selector with spamattr
        with self.assertRaises(ValueError) as cm:
            Domain(spamattr='eggvalue').to_xml_selector()

    def testMailboxFromXML(self):
        m = Mailbox.from_xml(self.mbox)
        self.assertIsInstance(m, Mailbox)
        self.assertIsInstance(m.newMessages, str)


    def test_ZObjects_import_a_tags(self):
        props = Domain._parse_a_tags(self.simple_domain)
        self.assertIsInstance(props, dict)
        # 53 is the number of unique "n" keys in the sample domain.
        self.assertEqual(len(props), 53)
        # Just check one of the <a> tags
        self.assertEqual(props['zimbraAuthMech'], 'zimbra')

    def test_ZObjects_import_a_tags_multivalue(self):
        props = Domain._parse_a_tags(self.simple_domain)
        self.assertIsInstance(props['objectClass'], list)
        self.assertEqual(
            props['objectClass'],
            ['dcObject', 'organization', 'zimbraDomain', 'amavisAccount'])

    def test_ZObjects_access_a_tag_as_item(self):
        d = Domain.from_xml(self.simple_domain)
        self.assertEqual(d['zimbraAuthMech'], 'zimbra')

    def test_ZObjects_comparison_equals(self):
        d1 = Domain(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')
        d2 = Domain(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')
        self.assertTrue(d1 == d2)
        self.assertFalse(d1 != d2)

    def test_ZObjects_comparison(self):
        d1 = Domain(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')
        d2 = Domain(id='dddddddd-f000-440b-bce6-dddddddddddd')
        self.assertTrue(d1 != d2)
        self.assertFalse(d1 == d2)


    def test_ZObjects_comparison_invalid_id_first(self):
        d1 = Domain(id='123')
        d2 = Domain(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')

        with self.assertRaises(ValueError) as cm:
            d1 == d2

    def test_ZObjects_comparison_invalid_id_second(self):
        d1 = Domain(id='123')
        d2 = Domain(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')

        with self.assertRaises(ValueError) as cm:
            d2 == d1


    def test_ZObjects_comparison_invalid_type(self):
        d1 = Domain(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')
        m1 = Mailbox(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')

        with self.assertRaises(TypeError) as cm:
            d1 == m1

class ZimsoapUtilsTests(unittest.TestCase):
    def testExtractResponsesFilled(self):
        xml = SimpleXMLElement(samples.XML_MULTIPLE_RESPONSE_TAGS)
        response_content = zimsoap.utils.extractResponses(xml)
        self.assertEqual(len(response_content), 2)

    def testExtractResponsesEmpty(self):
        xml = SimpleXMLElement(samples.XML_EMPTY_RESPONSE_TAGS)
        response_content = zimsoap.utils.extractResponses(xml)
        self.assertIsInstance(response_content, (list, tuple))
        self.assertEqual(len(response_content), 0)

    def testValidZuuid(self):
        self.assertTrue(zimsoap.utils.is_zuuid(
                'd78fd9c9-f000-440b-bce6-ea938d40fa2d'))

    def testEmptyZuuid(self):
        self.assertFalse(zimsoap.utils.is_zuuid(''))

    def testInvalidZuuid(self):
        # Just missing a char
        self.assertFalse(zimsoap.utils.is_zuuid(
                'd78fd9c9-f000-440b-bce6-ea938d40fa2'))

    def test_build_preauth_str(self):
        """ Taken from http://wiki.zimbra.com/wiki/Preauth
        """
        res = zimsoap.utils.build_preauth_str(
            preauth_key = '6b7ead4bd425836e8cf0079cd6c1a05acc127acd07c8ee4b61023e19250e929c',
            account_name = 'john.doe@domain.com',
            timestamp = 1135280708088,
            expires = 0
            )
        self.assertIsInstance(res, str)
        self.assertEqual(res, 'b248f6cfd027edd45c5369f8490125204772f844')


class PythonicAPITests(unittest.TestCase):
    """ Tests the pythonic API, the one that should be accessed by someone using
    the library.
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
            self.zc.delete_distribution_list(DistributionList(name=self.TEST_DL_NAME))
        except pysimplesoap.client.SoapFault:
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

        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            self.zc.get_distribution_list(dl_req)

        dl = self.zc.create_distribution_list(name)
        self.assertIsInstance(dl, DistributionList)
        self.assertEqual(dl.name, name)

        dl_got = self.zc.get_distribution_list(dl_req)
        self.assertIsInstance(dl_got, DistributionList)

        self.zc.delete_distribution_list(dl_got)

        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            self.zc.get_distribution_list(dl)

    def test_delete_by_name(self):
        name = self.TEST_DL_NAME
        dl_req = DistributionList(name=name)
        dl_full = self.zc.create_distribution_list(name)
        self.zc.delete_distribution_list(dl_req)

        # List with such a name does not exist
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            self.zc.get_distribution_list(dl_req)

        # List with such an ID does not exist
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            self.zc.get_distribution_list(dl_full)

    def test_mk_auth_token_succeeds(self):
        user = Account(name='admin@{}'.format(TEST_DOMAIN1))
        tk = self.zc.mk_auth_token(user, 0)
        self.assertIsInstance(tk, str)

    def test_mk_auth_token_fails_if_no_key(self):
        user = Account(name='admin@{}'.format(TEST_DOMAIN2))

        with self.assertRaises(DomainHasNoPreAuthKey) as cm:
            self.zc.mk_auth_token(user, 0)

    def test_admin_get_logged_in_by(self):
        new_zc = ZimbraAdminClient(TEST_HOST, TEST_ADMIN_PORT)
        new_zc.get_logged_in_by(TEST_ADMIN_LOGIN, self.zc)
        self.assertTrue(new_zc._session.is_logged_in())
        self.assertTrue(new_zc._session.is_session_valid())


class RESTClientTest(unittest.TestCase):
    @classmethod
    def setUp(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAdminClient(TEST_HOST, TEST_ADMIN_PORT)
        cls.zc.login(TEST_ADMIN_LOGIN, TEST_ADMIN_PASSWORD)

        cls.lambda_account = Account(name=TEST_LAMBDA_USER)
        domain_name = cls.lambda_account.get_domain()
        cls.ph_key_domain1 = cls.zc.get_domain(domain_name)['zimbraPreAuthKey']


    def test_user_preauth_without_key_fails(self):
        with self.assertRaises(RESTClient.NoPreauthKeyProvided) as cm:
            c = AccountRESTClient(TEST_HOST)
            c.get_preauth_token(self.lambda_account.name)

    def test_user_preauth_returns_something(self):
        c = AccountRESTClient(TEST_HOST, preauth_key=self.ph_key_domain1)
        token = c.get_preauth_token(self.lambda_account.name)
        self.assertIsInstance(token, str)

    def test_user_preauth_with_wrong_user_fails(self):
        with self.assertRaises(RESTClient.RESTBackendError) as cm:
            c = AccountRESTClient(TEST_HOST, preauth_key=self.ph_key_domain1)
            c.get_preauth_token('idonotexist1234@'+TEST_DOMAIN1)

    def test_admin_preauth_returns_something(self):
        c = AdminRESTClient(TEST_HOST, preauth_key=self.ph_key_domain1)
        token = c.get_preauth_token(TEST_ADMIN_LOGIN)
        self.assertIsInstance(token, str)

    def test_admin_preauth_is_valid(self):
        c = AdminRESTClient(TEST_HOST, preauth_key=self.ph_key_domain1)
        token = c.get_preauth_token(TEST_ADMIN_LOGIN)

        self.zc._session.import_session(token)
        self.assertTrue(self.zc._session.is_session_valid())


def main():
    unittest.main()

if __name__ == '__main__':
    main()


