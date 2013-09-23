#!/usr/bin/env python

import unittest
import urllib2
from os.path import dirname, abspath, join


import pysimplesoap

from zimsoap.client import ZimbraAdminClient, ZimbraAPISession, ShouldAuthenticateFirst


class ZimbraAPISessionTests(unittest.TestCase):
    def setUp(self):
        WSDL_PATH = abspath(join(dirname(abspath(__file__)),
                                 'share/zimbra.wsdl'))

        self.cli = pysimplesoap.client.SoapClient(wsdl=WSDL_PATH)
        self.cli.services['ZimbraService']['ports']['ZimbraServicePort']['location']\
            = "https://zimbratest.oasiswork.fr:7071/service/admin/soap"
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

class ZimbraAdminReturnTypes(unittest.TestCase):
    def setUp(self):
        self.username = 'admin@zimbratest.oasiswork.fr'
        self.password = 'admintest'
        self.server = 'zimbratest.oasiswork.fr'

        self.obj_type = pysimplesoap.client.SoapClient.WSDL_OBJECT_RETURN_TYPE
        self.dict_type = pysimplesoap.client.SoapClient.WSDL_DICT_RETURN_TYPE

        # self.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        # self.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

    def login(self, zc):
        zc.login(self.username, self.password)

    def init_default_client(self):
        zc = ZimbraAdminClient(self.server)
        self.login(zc)
        return zc

    def testDictReturnType(self):
        zc = self.init_default_client()
        resp = zc.GetAllDomainsRequest(wsdl_return_type=self.dict_type)
        self.assertIsInstance(resp, list)

    def testObjectReturnType(self):
        zc = self.init_default_client()
        resp = zc.GetAllDomainsRequest(wsdl_return_type=self.obj_type)
        self.assertIsInstance(resp, pysimplesoap.simplexml.SimpleXMLElement)

    def testDefaultReturnTypeIsObj(self):
        zc = self.init_default_client()
        obj_type = pysimplesoap.client.SoapClient.WSDL_OBJECT_RETURN_TYPE
        resp = zc.GetAllDomainsRequest(wsdl_return_type=obj_type)
        resp2 = zc.GetAllDomainsRequest()
        self.assertEqual(repr(resp), repr(resp2))

    def testBadWSDLTypeFails(self):
        zc = self.init_default_client()
        bad_type = 42
        with self.assertRaises(TypeError) as cm:
            resp = zc.GetAllDomainsRequest(
                wsdl_return_type=42)


class ZimbraAdminClientRequests(unittest.TestCase):
    def setUp(self):
        self.zc = ZimbraAdminClient('zimbratest.oasiswork.fr', 7071)
        self.zc.login('admin@zimbratest.oasiswork.fr', 'admintest')

    def testGetAllAccountsReturnsSomething(self):
        resp = self.zc.GetAllAccountsRequest()
        self.assertIsInstance(resp, pysimplesoap.simplexml.SimpleXMLElement)

    def testGetAllAccountsReturnsSomething(self):
        resp = self.zc.GetAllAccountsRequest()
        self.assertIsInstance(resp, pysimplesoap.simplexml.SimpleXMLElement)

    def testGetAllDomainsReturnsSomething(self):
        resp = self.zc.GetAllDomainsRequest()
        self.assertIsInstance(resp, pysimplesoap.simplexml.SimpleXMLElement)

    def testGetAllDomainsReturnsDomains(self):
        resp = self.zc.GetAllDomainsRequest()
        for tag in resp.children():
            self.assertEqual(tag.get_name(), 'domain')

    # def testCountAccount(self):
    #     """Count accounts on the first of domains"""
    #     domains = self.zc.GetAllDomainsRequest()
    #     first_domain_name = domains.children()[0]['name']

    #     resp = self.zc.CountAccountRequest(
    #         {'domain'},
    #         request_mangle=zc.DomainSelectorByName()
    #         )
    #     print resp.as_xml(pretty=True)


def main():
    unittest.main()



if __name__ == '__main__':
    main()


