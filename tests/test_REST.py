""" Unittests against REST webservices (Zimbra)

It has to be tested against a zimbra server (see properties.py) and is only
supposed to pass with the reference VMs.
"""

import unittest

from zimsoap.client import *
from zimsoap.zobjects import *

from tests.properties import *

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
