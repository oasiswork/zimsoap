#!/usr/bin/env python

import unittest
import urllib2
from os.path import dirname, abspath, join


import pysimplesoap

from zimsoap.client import ZimbraAdminClient, ZimbraAPISession


class ZimbraAPISessionTests(unittest.TestCase):
    def setUp(self):
        WSDL_PATH = abspath(join(dirname(abspath(__file__)),
                                 'share/zimbra.wsdl'))

        self.cli = pysimplesoap.client.SoapClient(wsdl=WSDL_PATH)
        self.cli.services['ZimbraService']['ports']['ZimbraServicePort']['location']\
            = "https://zimbratest.oasiswork.fr:7071/service/admin/soap"


    def testInit(self):
        session = ZimbraAPISession(self.cli)
        self.assertFalse(session.is_logged_in())

    def testSuccessfullLogin(self):
        session = ZimbraAPISession(self.cli)
        session.login('admin@zimbratest.oasiswork.fr', 'admintest')
        self.assertTrue(session.is_logged_in())



class ZimbraAdminClientTests(unittest.TestCase):
    def testLogin(self):
        zc = ZimbraAdminClient('admin@zimbratest.oasiswork.fr', 'admintest',
                               'zimbratest.oasiswork.fr', 7071)
        self.assertTrue(zc.is_logged_in())

    def testBadLoginFailure(self):
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            zc = ZimbraAdminClient('badlogin@bar.com', 'admintest',
                                   'zimbratest.oasiswork.fr', 7071)

        self.assertEqual(cm.exception.faultcode, 'soap:Client')

    def testBadPasswordFailure(self):
        with self.assertRaises(pysimplesoap.client.SoapFault) as cm:
            zc = ZimbraAdminClient('admin@zimbratest.oasiswork.fr', 'badpass',
                                   'zimbratest.oasiswork.fr', 7071)

        self.assertEqual(cm.exception.faultcode, 'soap:Client')

    def testBadHostFailure(self):
        with self.assertRaises(urllib2.URLError) as cm:
            zc = ZimbraAdminClient('admin@zimbratest.oasiswork.fr', 'admintest',
                                   'badhost.baddomain.fr', 7071)

    def testBadPortFailure(self):
        with self.assertRaises(urllib2.URLError) as cm:
            zc = ZimbraAdminClient('admin@zimbratest.oasiswork.fr', 'admintest',
                                   'zimbratest.oasiswork.fr', 9999)

def main():
    unittest.main()



if __name__ == '__main__':
    main()


