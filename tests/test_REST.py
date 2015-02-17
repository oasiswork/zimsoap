""" Integration tests against REST webservices (Zimbra)

It has to be tested against a zimbra server (see README.md).
"""

import unittest

from zimsoap.client import *
from zimsoap.zobjects import *

import tests
TEST_CONF = tests.get_config()

class RESTClientTest(unittest.TestCase):
    @classmethod
    def setUp(cls):
        self.HOST = TEST_CONF['host']
        self.ADMIN_LOGIN = TEST_CONF['admin_login']

        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAdminClient(self.HOST, TEST_CONF['admin_port'])
        cls.zc.login(self.ADMIN_LOGIN, TEST_CONF['admin_password'])

        cls.lambda_account = Account(name=TEST_CONF['lambda_user'])
        domain_name = cls.lambda_account.get_domain()
        cls.ph_key_domain1 = cls.zc.get_domain(domain_name)['zimbraPreAuthKey']


    def test_user_preauth_without_key_fails(self):
        with self.assertRaises(RESTClient.NoPreauthKeyProvided) as cm:
            c = AccountRESTClient(self.HOST)
            c.get_preauth_token(self.lambda_account.name)

    def test_user_preauth_returns_something(self):
        c = AccountRESTClient(self.HOST, preauth_key=self.ph_key_domain1)
        token = c.get_preauth_token(self.lambda_account.name)
        self.assertIsInstance(token, str)

    def test_user_preauth_with_wrong_user_fails(self):
        with self.assertRaises(RESTClient.RESTBackendError) as cm:
            c = AccountRESTClient(self.HOST, preauth_key=self.ph_key_domain1)
            c.get_preauth_token('idonotexist1234@'+TEST_CONF['domain1'])

    def test_admin_preauth_returns_something(self):
        c = AdminRESTClient(self.HOST, preauth_key=self.ph_key_domain1)
        token = c.get_preauth_token(self.ADMIN_LOGIN)
        self.assertIsInstance(token, str)

    def test_admin_preauth_is_valid(self):
        c = AdminRESTClient(self.HOST, preauth_key=self.ph_key_domain1)
        token = c.get_preauth_token(self.ADMIN_LOGIN)

        self.zc._session.import_session(token)
        self.assertTrue(self.zc._session.is_session_valid())
