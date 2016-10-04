#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals


""" Integration tests against zimbraAccount SOAP webservice

It has to be tested against a zimbra server (see README.md)
"""

import unittest

from six import text_type, binary_type

from zimsoap import utils
from zimsoap.client import (
    ZimbraAccountClient,
    ZimbraSoapServerError,
    ZimbraMailClient,
    ZimbraAdminClient
)
from zimsoap.zobjects import Signature, Identity, Account
import tests

TEST_CONF = tests.get_config()


class ZimbraAccountClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAccountClient(TEST_CONF['host'])
        cls.zc.login(TEST_CONF['lambda_user'], TEST_CONF['lambda_password'])

    def tearDown(self):
        # Delete the test signature (if any)
        for signame in ('unittest', 'renamed-unittest'):
            try:
                self.zc.request('DeleteSignature', {
                    'signature': {'name': signame}
                })

            except ZimbraSoapServerError as e:
                if 'no such signature' in str(e):
                    pass

                else:
                    raise

    def testGetSignaturesReturnsSomething(self):
        resp = self.zc.request('GetSignatures')
        self.assertEqual(resp, {})

        # Normally, the user has no signature by default
        self.assertFalse('signature' in resp)

    def testCreateSignatureReturnsSomething(self):
        resp = self.zc.request('CreateSignature', {
            'signature': {
                'name': 'unittest',
                'content':
                {'type': 'text/plain', '_content': 'TEST SIGNATURE'}
            }
        })

        sig = resp['signature']
        self.assertEqual(sig['name'], 'unittest')
        return sig

    def testDeleteSignatureReturnsProperly(self):
        self.testCreateSignatureReturnsSomething()
        self.zc.request('DeleteSignature', {
            'signature': {'name': 'unittest'}})

    def testModifySignatureWorks(self):
        sig = self.testCreateSignatureReturnsSomething()

        self.zc.request('ModifySignature', {
            'signature': {
                'id': sig['id'],
                'content': {'type': 'text/plain', '_content': 'MODIFSIG'}
            }
        })

        resp_getsig = self.zc.request('GetSignatures')
        sig = resp_getsig['signature']

        # is there only one signature
        self.assertIsInstance(sig, dict)
        self.assertEqual('MODIFSIG', sig['content']['_content'])

    def testGetAllPreferences(self):
        resp = self.zc.request('GetPrefs')
        self.assertIn('pref', resp)
        prefs = resp['pref']
        self.assertIsInstance(prefs, list)

    def testGetAPreference(self):
        resp = self.zc.request('GetPrefs',
                               {'pref': {'name': 'zimbraPrefMailFlashTitle'}})

        pref = resp['pref']

        self.assertIsInstance(pref, dict)
        self.assertEqual(pref['name'], 'zimbraPrefMailFlashTitle')

    def testCreateGetModifyDeleteIdentity(self):
        # Create
        i = self.zc.create_identity(name='test-identity', attrs=[{
            'name': 'zimbraPrefWhenInFoldersEnabled',
            '_content': 'TRUE'
        }])

        # Get
        get_i = self.zc.get_identities(identity='test-identity')[0]
        # Verify create and get
        self.assertEqual(i, get_i)

        # Modify 1
        from_addr = 'anothersender@example.com'

        i = self.zc.modify_identity(
            identity='test-identity', zimbraPrefFromAddress=from_addr)
        self.assertEqual(i._a_tags['zimbraPrefFromAddress'], from_addr)

        # Modify 2
        # clean (needed with use of zobjects.Identity to avoid illegal
        # multivalue attribute)
        i._full_data['a'].remove({
            'name': 'zimbraPrefFromAddress',
            '_content': from_addr})
        from_addr = 'someaddress@example.com'
        i._full_data['a'].append({
            'name': 'zimbraPrefFromAddress',
            '_content': from_addr})
        mod_i = self.zc.modify_identity(i)
        self.assertEqual(mod_i._a_tags['zimbraPrefFromAddress'], from_addr)

        # Delete 1
        self.zc.delete_identity(mod_i)

        self.assertEqual(self.zc.get_identities(identity=mod_i), [])

        # Delete 2
        i = self.zc.create_identity(name='test-identity', attrs={
            'zimbraPrefWhenInFoldersEnabled': 'TRUE'})
        self.zc.delete_identity(identity='test-identity')

        self.assertEqual(self.zc.get_identities(i), [])

    def testAddRemoveGetBlackWhiteLists(self):
        addr = 'test@external.com'
        self.zc.add_to_blacklist([addr])
        wbl = self.zc.get_white_black_lists()
        self.assertEqual(wbl['blackList']['addr'], addr)

        self.zc.remove_from_blacklist([addr])
        wbl = self.zc.get_white_black_lists()
        self.assertEqual(wbl['blackList'], {})

        self.zc.add_to_whitelist([addr])
        wbl = self.zc.get_white_black_lists()
        self.assertEqual(wbl['whiteList']['addr'], addr)

        self.zc.remove_from_whitelist([addr])
        wbl = self.zc.get_white_black_lists()
        self.assertEqual(wbl['whiteList'], {})


class PythonicAccountAPITests(unittest.TestCase):
    """ Tests the pythonic API, the one that should be accessed by someone using
    the library, zimbraAccount features.
    """

    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAccountClient(TEST_CONF['host'])
        cls.zc.login(TEST_CONF['lambda_user'], TEST_CONF['lambda_password'])

    def tearDown(self):
        # Delete the test signature (if any)
        for i in ('unittest', 'unittest1'):
            try:
                self.zc.request('DeleteSignature', {'signature': {'name': i}})
            except ZimbraSoapServerError as e:
                if 'no such signature' in str(e):
                    pass
                else:
                    raise

    def test_create_signature(self):
        sig_name = 'unittest'
        sig_content = 'TEST CONTENT'
        sig = self.zc.create_signature(sig_name, sig_content)

        self.assertIsInstance(sig, Signature)
        self.assertTrue(utils.is_zuuid(sig.id))
        self.assertEqual(sig.name, sig_name)
        return sig

    def test_create_signature_with_xml_content(self):
        sig_name = 'unittest'
        sig_content = '&nbsp;'
        sig = self.zc.create_signature(sig_name, sig_content)

        self.assertIsInstance(sig, Signature)
        self.assertTrue(utils.is_zuuid(sig.id))
        self.assertEqual(sig.name, sig_name)
        return sig

    def test_delete_signature_by_name(self):
        sig = self.test_create_signature()
        self.zc.delete_signature(Signature(id=sig.id))

    def test_delete_signature_by_id(self):
        sig = self.test_create_signature()
        self.zc.delete_signature(Signature(name=sig.name))

    def test_get_all_signatures_empty(self):
        resp = self.zc.get_signatures()
        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 0)

    def test_get_all_signatures_onlyone(self):
        self.zc.create_signature('unittest', 'CONTENT', "text/html")

        resp = self.zc.get_signatures()
        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        a_sig = resp[0]
        self.assertIsInstance(a_sig, Signature)
        self.assertEqual(a_sig.name, 'unittest')
        self.assertEqual(a_sig.get_content(), 'CONTENT')
        self.assertEqual(a_sig.get_content_type(), 'text/html')

    def test_get_all_signatures_nonempty(self):
        self.zc.create_signature('unittest', 'CONTENT', "text/html")
        self.zc.create_signature('unittest1', 'CONTENT', "text/html")

        resp = self.zc.get_signatures()
        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 2)

        a_sig = resp[0]
        self.assertIsInstance(a_sig, Signature)
        self.assertEqual(a_sig.name, 'unittest')
        self.assertEqual(a_sig.get_content(), 'CONTENT')
        self.assertEqual(a_sig.get_content_type(), 'text/html')

    def test_create_signature_special_char(self):
        self.zc.create_signature('unittest', '&nbsp;', "text/html")

        resp = self.zc.get_signatures()
        self.assertIsInstance(resp, list)
        self.assertEqual(len(resp), 1)

        a_sig = resp[0]
        self.assertIsInstance(a_sig, Signature)
        self.assertEqual(a_sig.name, 'unittest')
        self.assertEqual(a_sig.get_content(), '&nbsp;')
        self.assertEqual(a_sig.get_content_type(), 'text/html')

    def test_get_a_signature_by_signature(self):
        sig1 = self.zc.create_signature('unittest', 'CONTENT', "text/html")
        sig2 = self.zc.create_signature('unittest1', 'CONTENT', "text/html")

        resp = self.zc.get_signature(sig1)
        self.assertIsInstance(resp, Signature)
        self.assertEqual(resp, sig1)

        resp = self.zc.get_signature(sig2)
        self.assertIsInstance(resp, Signature)
        self.assertEqual(resp, sig2)

    def test_get_a_signature_by_name(self):
        sig1 = self.zc.create_signature('unittest', 'CONTENT', "text/html")
        self.zc.create_signature('unittest1', 'CONTENT', "text/html")

        resp = self.zc.get_signature(Signature(name='unittest'))
        self.assertIsInstance(resp, Signature)
        self.assertEqual(resp, sig1)

    def test_get_a_signature_by_name_case_insensitive(self):
        """ Zimbra considers that the signature name should be unique

        two signatures with same name, diferently cased is not allowed, so it's
        logical to be able to query a signature with any case.
        """
        sig1 = self.zc.create_signature('unittest', 'CONTENT', "text/html")
        self.zc.create_signature('unittest1', 'CONTENT', "text/html")

        resp = self.zc.get_signature(Signature(name='unitTEST'))
        self.assertIsInstance(resp, Signature)
        self.assertEqual(resp, sig1)

    def test_get_a_signature_by_nonexistant_name_returns_none(self):
        resp = self.zc.get_signature(Signature(name='idonotexist'))
        self.assertEqual(resp, None)

    def test_get_a_signature_by_nonexistant_id_returns_none(self):
        resp = self.zc.get_signature(Signature(
            id='42428c6a-d764-479f-ae7d-d2d626b44242'))
        self.assertEqual(resp, None)

    def test_get_a_signature_by_id(self):
        sig1 = self.zc.create_signature('unittest', 'CONTENT', "text/html")
        sig2 = self.zc.create_signature('unittest1', 'CONTENT', "text/html")

        resp = self.zc.get_signature(Signature(id=sig1.id))
        self.assertIsInstance(resp, Signature)
        self.assertEqual(resp, sig1)

        resp = self.zc.get_signature(Signature(id=sig2.id))
        self.assertIsInstance(resp, Signature)
        self.assertEqual(resp, sig2)

    def test_modify_signature_content(self):
        sig1 = self.zc.create_signature('unittest', 'CONTENT', "text/html")
        sig1.set_content('NEW-CONTENT', "text/plain")
        self.zc.modify_signature(sig1)
        modified_sig1 = self.zc.get_signature(sig1)
        self.assertEqual(modified_sig1.name, 'unittest')
        self.assertEqual(modified_sig1.get_content(), 'NEW-CONTENT')
        self.assertEqual(modified_sig1._contenttype, 'text/plain')

    def test_modify_signature_name(self):
        sig1 = self.zc.create_signature('unittest', 'CONTENT', "text/html")
        sig1.name = 'renamed-unittest'
        self.zc.modify_signature(sig1)
        modified_sig1 = self.zc.get_signature(sig1)
        self.assertEqual(modified_sig1.name, 'renamed-unittest')
        self.assertEqual(modified_sig1.get_content(), 'CONTENT')
        self.assertEqual(modified_sig1._contenttype, 'text/html')

        # Rename it back to be sure it gets deleted in tearDown
        modified_sig1.name = 'unittest'
        self.zc.modify_signature(modified_sig1)

    def test_modify_signature_without_id_attribute_error(self):
        sig1 = Signature(name='foo')
        sig1.set_content('NEW-CONTENT', "text/plain")
        with self.assertRaises(AttributeError):
            self.zc.modify_signature(sig1)

    def test_get_preference(self):
        resp = self.zc.get_preference('zimbraPrefMailFlashTitle')
        self.assertIsInstance(resp, bool)
        resp = self.zc.get_preference('zimbraPrefComposeFormat')
        self.assertIsInstance(resp, (text_type, binary_type))
        resp = self.zc.get_preference('zimbraPrefCalendarDayHourEnd')
        self.assertIsInstance(resp, int)

    def test_get_preferences(self):
        prefs = self.zc.get_preferences()
        self.assertIsInstance(prefs, dict)
        self.assertIsInstance(prefs['zimbraPrefMailFlashTitle'], bool)
        self.assertIsInstance(prefs['zimbraPrefComposeFormat'],
                              (text_type, binary_type))
        self.assertIsInstance(prefs['zimbraPrefCalendarDayHourEnd'], int)

    def test_get_identities(self):
        identities = self.zc.get_identities()
        self.assertIsInstance(identities, list)
        self.assertIsInstance(identities[0], Identity)
        self.assertEqual(identities[0].name, 'DEFAULT')
        self.assertTrue(utils.is_zuuid(identities[0]['zimbraPrefIdentityId']))

    def test_account_get_logged_in_by(self):
        admin_zc = ZimbraAdminClient(TEST_CONF['host'],
                                     TEST_CONF['admin_port'])
        admin_zc.login(TEST_CONF['admin_login'], TEST_CONF['admin_password'])

        new_zc = ZimbraAccountClient(TEST_CONF['host'])
        new_zc.get_logged_in_by(TEST_CONF['lambda_user'], admin_zc)

        self.assertTrue(new_zc._session.is_logged_in())
        self.assertTrue(new_zc.is_session_valid())

    def test_account_delegated_login(self):
        admin_zc = ZimbraAdminClient(TEST_CONF['host'],
                                     TEST_CONF['admin_port'])
        admin_zc.login(TEST_CONF['admin_login'], TEST_CONF['admin_password'])

        new_zc = ZimbraAccountClient(TEST_CONF['host'])
        new_zc.delegated_login(TEST_CONF['lambda_user'], admin_zc)

        self.assertTrue(new_zc._session.is_logged_in())
        self.assertTrue(new_zc.is_session_valid())

    def test_get_share_info(self):

        # No shares yes
        shares = self.zc.get_share_info()
        self.assertEqual(shares, [])

        # Create share
        admin_zc = ZimbraAdminClient(TEST_CONF['host'],
                                     TEST_CONF['admin_port'])
        admin_zc.login(TEST_CONF['admin_login'], TEST_CONF['admin_password'])
        mail_zc2 = ZimbraMailClient(
            TEST_CONF['host'], TEST_CONF['webmail_port'])
        mail_zc2.delegated_login(TEST_CONF['lambda_user2'], admin_zc)

        mail_zc2.modify_folder_grant(
                folder_ids=['1'],
                grantee_name=TEST_CONF['lambda_user'],
                perm='rwixd',
                gt='usr'
            )

        shares = self.zc.get_share_info()
        self.assertEqual(shares[0]['ownerEmail'], TEST_CONF['lambda_user2'])

        # Clean
        mail_zc2.modify_folder_grant(
                folder_ids=['1'],
                zid=admin_zc.get_account(
                    Account(name=TEST_CONF['lambda_user'])).id,
                perm='none',
                gt='usr'
            )
