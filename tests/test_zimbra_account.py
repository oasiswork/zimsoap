#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unittests against zimbraAccount SOAP webservice

It has to be tested against a zimbra server (see properties.py) and is only
supposed to pass with the reference VMs.
"""

import unittest

from zimsoap.client import *
from zimsoap.zobjects import *

from tests.properties import *

class ZimbraAccountClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAccountClient(TEST_HOST)
        cls.zc.login(TEST_LAMBDA_USER, TEST_LAMBDA_PASSWORD)

    def tearDown(self):
        # Delete the test signature (if any)
        for signame in ('unittest', 'renamed-unittest'):
            try:
                resp = self.zc.request('DeleteSignature', {
                        'signature': {'name': signame}})

            except ZimbraSoapServerError, e:
                if 'no such signature' in str(e):
                    pass

                else:
                    raise

    def testGetSignaturesReturnsSomething(self):
        resp = self.zc.request('GetSignatures')
        self.assertEqual(resp['xmlns'], 'urn:zimbraAccount')

        # Normally, the user has no signature by default
        self.assertFalse(resp.has_key('signature'))

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
        sig = self.testCreateSignatureReturnsSomething()
        resp = self.zc.request('DeleteSignature', {
                'signature': {'name': 'unittest'}})

    def testModifySignatureWorks(self):
        sig = self.testCreateSignatureReturnsSomething()

        resp = self.zc.request('ModifySignature', {
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
        prefs = resp['pref']
        self.assertTrue(resp.has_key('pref'))
        self.assertIsInstance(resp['pref'], list)

    def testGetAPreference(self):
        resp = self.zc.request('GetPrefs',
                               {'pref': {'name': 'zimbraPrefMailFlashTitle'}})

        pref = resp['pref']

        self.assertIsInstance(pref, dict)
        self.assertEqual(pref['name'], 'zimbraPrefMailFlashTitle')

    def testGetIdentities(self):
        identities = self.zc.request('GetIdentities')

        # only one
        self.assertIsInstance(identities['identity'], dict)

    def modifyIdentity(self):
        resp1 = self.zc.request('ModifyIdentity', {'identity': {
                    'name': 'DEFAULT',
                    'a': {'name': 'zimbraPrefSaveToSent', '_content': 'FALSE' }
        }})

        resp2 = self.zc.request('ModifyIdentity', {'identity': {
                    'name': 'DEFAULT',
                    'a': {'name': 'zimbraPrefSaveToSent', '_content': 'TRUE' }
        }})

        # just checks that it succeeds


class PythonicAccountAPITests(unittest.TestCase):
    """ Tests the pythonic API, the one that should be accessed by someone using
    the library, zimbraAccount features.
    """

    @classmethod
    def setUpClass(cls):
        # Login/connection is done at class initialization to reduce tests time
        cls.zc = ZimbraAccountClient(TEST_HOST)
        cls.zc.login(TEST_LAMBDA_USER, TEST_LAMBDA_PASSWORD)

    def tearDown(self):
        # Delete the test signature (if any)
        for i in ('unittest', 'unittest1'):
            try:
                self.zc.request('DeleteSignature', {'signature': {'name': i}})
            except ZimbraSoapServerError, e:
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

    def test_get_a_signature_by_name(self):
        sig1 = self.zc.create_signature('unittest', 'CONTENT', "text/html")
        sig2 = self.zc.create_signature('unittest1', 'CONTENT', "text/html")

        resp = self.zc.get_signature(Signature(name='unittest'))
        self.assertIsInstance(resp, Signature)
        self.assertEqual(resp, sig1)

    def test_get_a_signature_by_nonexistant_name_returns_none(self):
        resp = self.zc.get_signature(Signature(name='idonotexist'))
        self.assertEqual(resp, None)

    def test_get_a_signature_by_id(self):
        sig1 = self.zc.create_signature('unittest', 'CONTENT', "text/html")
        sig2 = self.zc.create_signature('unittest1', 'CONTENT', "text/html")

        resp = self.zc.get_signature(Signature(id=sig1.id))
        self.assertIsInstance(resp, Signature)
        self.assertEqual(resp, sig1)

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
        with self.assertRaises(AttributeError) as cm:
            self.zc.modify_signature(sig1)

    def test_get_preference(self):
        resp = self.zc.get_preference('zimbraPrefMailFlashTitle')
        self.assertIsInstance(resp, bool)
        resp = self.zc.get_preference('zimbraPrefComposeFormat')
        self.assertIsInstance(resp, (str, unicode))
        resp = self.zc.get_preference('zimbraPrefCalendarDayHourEnd')
        self.assertIsInstance(resp, int)

    def test_get_preferences(self):
        prefs = self.zc.get_preferences()
        self.assertIsInstance(prefs, dict)
        self.assertIsInstance(prefs['zimbraPrefMailFlashTitle'], bool)
        self.assertIsInstance(prefs['zimbraPrefComposeFormat'], (str, unicode))
        self.assertIsInstance(prefs['zimbraPrefCalendarDayHourEnd'], int)

    def test_get_identities(self):
        identities = self.zc.get_identities()
        self.assertIsInstance(identities, list)
        self.assertIsInstance(identities[0], Identity)
        self.assertEqual(identities[0].name, 'DEFAULT')
        self.assertTrue(utils.is_zuuid(identities[0]['zimbraPrefIdentityId']))

    def test_modify_identity(self):
        test_attr = 'zimbraPrefFromDisplay'

        # First get the default identity id
        def_identity = self.zc.get_identities()[0]

        initial_attrval = def_identity[test_attr]

        i = Identity(id=def_identity.id)
        i[test_attr] = 'Patapon'
        self.zc.modify_identity(i)

        modified_i = self.zc.get_identities()[0]
        self.assertEqual(modified_i[test_attr], 'Patapon')

        # Revert it back
        i[test_attr] = initial_attrval
        self.zc.modify_identity(i)


    def test_account_get_logged_in_by(self):
        admin_zc = ZimbraAdminClient(TEST_HOST, TEST_ADMIN_PORT)
        admin_zc.login(TEST_ADMIN_LOGIN, TEST_ADMIN_PASSWORD)

        new_zc = ZimbraAccountClient(TEST_HOST)
        new_zc.get_logged_in_by(TEST_LAMBDA_USER, admin_zc)

        self.assertTrue(new_zc._session.is_logged_in())
        self.assertTrue(new_zc._session.is_session_valid())
