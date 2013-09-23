#!/usr/bin/env python

import unittest
import urllib2
from os.path import dirname, abspath, join


import pysimplesoap
from pysimplesoap.client import SimpleXMLElement

import zimsoap.utils
from zimsoap.tests import samples
from zimsoap.client import ZimbraAdminClient, ZimbraAPISession, ShouldAuthenticateFirst
from zimsoap.zobjects import *


class ZimbraAPISessionTests(unittest.TestCase):
    def setUp(self):
        # WSDL_PATH = abspath(join(dirname(abspath(__file__)),
        #                          'share/zimbra.wsdl'))

        loc = "https://zimbratest.oasiswork.fr:7071/service/admin/soap"
        self.cli = pysimplesoap.client.SoapClient(location=loc, action=loc,
                                                  namespace='urn:zimbraAdmin', ns=False)
        # self.cli.services['ZimbraService']['ports']['ZimbraServicePort']['location']\
        #     =
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
    def testLogin(self):
        zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        zc.login('admin@zimbratest.oasiswork.fr', 'admintest')
        self.assertTrue(zc._session.is_logged_in())

    def testBadLoginFailure(self):
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
            zc.login('badlogin@zimbratest.oasiswork.fr', 'admintest')

        self.assertEqual(cm.exception.faultcode, 'soap:Client')

    def testBadPasswordFailure(self):
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
            zc.login('admin@zimbratest.oasiswork.fr', 'badpassword')

        self.assertEqual(cm.exception.faultcode, 'soap:Client')

    def testBadHostFailure(self):
        with self.assertRaises(urllib2.URLError) as cm:
            zc = ZimbraAdminClient('nonexistenthost.oasiswork.fr', 7071)
            zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

    def testBadPortFailure(self):
        with self.assertRaises(urllib2.URLError) as cm:
            zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 9999)
            zc.login('admin@zimbratest.oasiswork.fr', 'admintest')


class ZimbraAdminClientRequests(unittest.TestCase):
    def setUp(self):
        self.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        self.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

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

#     # def testCountAccount(self):
#     #     """Count accounts on the first of domains"""
#     #     domains = self.zc.GetAllDomainsRequest()
#     #     first_domain_name = domains.children()[0]['name']

#     #     resp = self.zc.CountAccountRequest(
#     #         {'domain'},
#     #         request_mangle=zc.DomainSelectorByName()
#     #         )
#     #     print resp.as_xml(pretty=True)


class ZObjectsTests(unittest.TestCase):
    def setUp(self):
        self.simple_domain = SimpleXMLElement(samples.SIMPLE_DOMAIN)
        self.misnamed_domain = SimpleXMLElement(samples.MISNAMED_DOMAIN)

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


def main():
    unittest.main()

if __name__ == '__main__':
    main()


