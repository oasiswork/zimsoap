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
from zimsoap.client import ZimbraAdminClient, ZimbraAPISession, ShouldAuthenticateFirst
from zimsoap.zobjects import *


class ZimbraAPISessionTests(unittest.TestCase):
    def setUp(self):
        loc = "https://zimbratest.oasiswork.fr:7071/service/admin/soap"
        self.cli = pysimplesoap.client.SoapClient(location=loc, action=loc,
                                                  namespace='urn:zimbraAdmin', ns=False)
        self.session = ZimbraAPISession(self.cli)

    def testInit(self):
        self.session = ZimbraAPISession(self.cli)
        self.assertFalse(self.session.is_logged_in())

    def testSuccessfullLogin(self):
        self.session.login('admin@zimbratest.oasiswork.fr', 'admintest')

        self.assertTrue(self.session.is_logged_in())

    def testHeader(self):
        self.session.login('admin@zimbratest.oasiswork.fr', 'admintest')
        self.session.get_context_header()

    def testHeaderNotLogged(self):
        with self.assertRaises(ShouldAuthenticateFirst) as cm:
            self.session.get_context_header()


class ZimbraAdminClientTests(unittest.TestCase):
    def setUp(self):
        self.TEST_SERVER = 'zimbratest.oasiswork.fr'
        self.TEST_LOGIN = 'admin@zimbratest.oasiswork.fr'
        self.TEST_PASSWORD = 'admintest'

    def testLogin(self):
        zc = ZimbraAdminClient(self.TEST_SERVER, 7071)
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


class ZimbraAdminClientRequests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        cls.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')


    def setUp(self):
        # self.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        # self.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

        self.EXISTANT_DOMAIN = "client1.unbound.oasiswork.fr"
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
        xml_node = SimpleXMLElement(
            '<l><mbox id="%s" /></l>' % self.EXISTANT_MBOX_ID)

        resp = self.zc.GetMailboxRequest(self.zc, xml_node)
        first_mbox = zimsoap.utils.extractResponses(resp)[0]
        self.assertEqual(first_mbox.get_name(), 'mbox')
        self.assertTrue(first_mbox.attributes().has_key('mbxid'))


    def testGetAllMailboxes(self):
        resp = self.zc.GetAllMailboxesRequest()
        mailboxes = zimsoap.utils.extractResponses(resp)
        self.assertEqual(mailboxes[0].get_name(), 'mbox')

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
        self.assertEqual(d.id, "b37d6b98-dc8c-474a-9243-f5dfc3ecf6ac")
        self.assertEqual(d.name, "client1.unbound.oasiswork.fr")

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
    def testValidZuuid(self):
        self.assertTrue(zimsoap.utils.is_zuuid(
                'd78fd9c9-f000-440b-bce6-ea938d40fa2d'))

    def testEmptyZuuid(self):
        self.assertFalse(zimsoap.utils.is_zuuid(''))

    def testInvalidZuuid(self):
        # Just missing a char
        self.assertFalse(zimsoap.utils.is_zuuid(
                'd78fd9c9-f000-440b-bce6-ea938d40fa2'))



class PythonicAPITests(unittest.TestCase):
    """ Tests the pythonic API, the one that should be accessed by someone using
    the library.
    """

    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        cls.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

    def setUp(self):
        # self.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        # self.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

        self.EXISTANT_DOMAIN = "client1.unbound.oasiswork.fr"
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


def main():
    unittest.main()

if __name__ == '__main__':
    main()


