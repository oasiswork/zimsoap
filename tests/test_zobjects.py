#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Unittests for zimsoap.zobjects """

import unittest

from six import text_type, binary_type

import zimsoap.utils
from zimsoap.zobjects import ZObject
from zimsoap.zobjects.admin import Account, Domain, Mailbox
from zimsoap.zobjects.account import Identity, Signature
from . import samples


class ZObjectsTests(unittest.TestCase):

    class NullZObject(ZObject):
        ATTRNAME_PROPERTY = 'n'
        TAG_NAME = 'TestObject'

    def setUp(self):
        # samples, as dict
        xml2dict = zimsoap.utils.xml_str_to_dict
        self.simple_domain_dict = xml2dict(samples.SIMPLE_DOMAIN)
        self.misnamed_domain_dict = xml2dict(samples.MISNAMED_DOMAIN)
        self.mbox_dict = xml2dict(samples.MBOX)
        self.admin_account_dict = xml2dict(samples.ADMIN_ACCOUNT)
        self.system_account_dict = xml2dict(samples.SYSTEM_ACCOUNT)
        self.normal_account_dict = xml2dict(samples.NORMAL_ACCOUNT)
        self.signature_dict = xml2dict(samples.SIGNATURE)
        self.identity_dict = xml2dict(samples.IDENTITY)

    def testZobjectNeverFailsToPrint(self):
        zo = self.NullZObject()
        self.assertIn(self.NullZObject.__name__, str(zo))
        zo.id = 'myid'
        self.assertIn('myid', str(zo))
        zo.name = 'myname'
        self.assertIn('myname', str(zo))

    def testZobjectNeverFailsToRepr(self):
        zo = self.NullZObject()
        self.assertIn(self.NullZObject.__name__, repr(zo))
        self.assertIn(hex(id(zo)), repr(zo))
        zo.id = 'myid'
        self.assertIn('myid', repr(zo))
        zo.name = 'myname'
        self.assertIn('myid', repr(zo))

    def testDomainFromDict(self):
        data = self.simple_domain_dict['domain']
        d = Domain.from_dict(data)
        self.assertIsInstance(d, Domain)
        self.assertIsInstance(d.id, text_type)
        self.assertIsInstance(d.name, text_type)
        self.assertIsNotNone(d.id)
        self.assertEqual(d.name, 'client1.unbound.example.com')
        self.assertEqual(d.get_full_data(), data)

    def testDomainSelector(self):
        d = Domain(name='foo')
        s = d.to_selector()
        self.assertEqual(s['by'], 'name')
        self.assertEqual(s['_content'], 'foo')

    def testInvalidDomainSelector(self):
        with self.assertRaises(ValueError):
            Domain().to_selector()

        # Should not produce a selector with spamattr
        with self.assertRaises(ValueError):
            Domain(spamattr='eggvalue').to_selector()

    def test_ZObjects_import_a_tags(self):
        props = Domain._parse_a_tags(self.simple_domain_dict['domain'])
        self.assertIsInstance(props, dict)
        # 53 is the number of unique "n" keys in the sample domain.
        self.assertEqual(len(props), 53)
        # Just check one of the <a> tags
        self.assertEqual(props['zimbraAuthMech'], 'zimbra')

    def test_ZObjects_get_single_tag_list(self):
        contact_dic = {'a': {'_content': 'test@example.com', 'n': 'email'},
                       'l': '7',
                       'd': '1445446429000',
                       'id': '298',
                       'rev': '24825',
                       'fileAsStr': ''}
        props = self.NullZObject._parse_a_tags(contact_dic)
        self.assertEqual(props['email'], 'test@example.com')

    def test_ZObjects_import_a_tags_multivalue(self):
        props = Domain._parse_a_tags(self.simple_domain_dict['domain'])
        self.assertIsInstance(props['objectClass'], list)
        self.assertEqual(
            props['objectClass'],
            ['dcObject', 'organization', 'zimbraDomain', 'amavisAccount'])

    def test_ZObjects_access_a_tag_as_item(self):
        d = Domain.from_dict(self.simple_domain_dict['domain'])
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

        with self.assertRaises(ValueError):
            d1 == d2

    def test_ZObjects_comparison_invalid_id_second(self):
        d1 = Domain(id='123')
        d2 = Domain(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')

        with self.assertRaises(ValueError):
            d2 == d1

    def test_ZObjects_comparison_invalid_type(self):
        d1 = Domain(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')
        m1 = Mailbox(id='d78fd9c9-f000-440b-bce6-ea938d40fa2d')

        with self.assertRaises(TypeError):
            d1 == m1

    def test_Signature_to_selector(self):
        s = Signature(id='1234')
        self.assertEqual(s.to_selector(), {'id': '1234'})
        self.assertIsInstance(s.to_selector(), dict)

        s = Signature(name='jdoe')
        self.assertEqual(s.to_selector(), {'name': 'jdoe'})

        s = Signature(id='1234', name='jdoe')
        self.assertEqual(s.to_selector(), {'id': '1234'})

    def test_Signature_creator_fails_without_content(self):
        s = Signature(name='unittest')
        with self.assertRaises(AttributeError):
            s.to_xml_creator()

    def test_Signature_creator_default_format(self):
        s = Signature(name='unittest')
        s.set_content('TEST_CONTENT')
        self.assertEqual(s._contenttype, 'text/html')

    def test_Signature_set_content(self):
        s = Signature(name='unittest')
        s.set_content('TEST_CONTENT', contenttype='text/plain')

        self.assertEqual(s._contenttype, 'text/plain')
        self.assertEqual(s._content, 'TEST_CONTENT')

    def test_Signature_creator_success(self):
        s = Signature(name='unittest')
        s.set_content('TEST_CONTENT', contenttype='text/plain')
        d = s.to_creator()
        self.assertTrue(d['content'], 'TEST_CONTENT')

    def test_Signature_dict_import(self):
        s = Signature.from_dict(self.signature_dict['signature'])
        self.assertIsInstance(s, Signature)
        self.assertIsInstance(s.get_content(), (text_type, binary_type))
        self.assertEqual(s.get_content(), 'CONTENT')
        self.assertEqual(s.get_content_type(), 'text/html')

    def test_Identity_to_creator(self):
        test_attr = 'zimbraPrefForwardReplyPrefixChar'

        i = Identity.from_dict(self.identity_dict['identity'])
        dict_again = Identity.from_dict(i.to_creator())
        self.assertEqual(i[test_attr], dict_again[test_attr])

    def test_Account_system(self):
        sys = Account.from_dict(self.system_account_dict['account'])
        norm = Account.from_dict(self.normal_account_dict['account'])
        adm = Account.from_dict(self.admin_account_dict['account'])

        self.assertEqual(sys.is_system(), True)
        self.assertEqual(adm.is_system(), False)
        self.assertEqual(norm.is_system(), False)

    def test_Account_admin(self):
        sys = Account.from_dict(self.system_account_dict['account'])
        norm = Account.from_dict(self.normal_account_dict['account'])
        adm = Account.from_dict(self.admin_account_dict['account'])

        self.assertEqual(sys.is_admin(), False)
        self.assertEqual(adm.is_admin(), True)
        self.assertEqual(norm.is_admin(), False)

    def test_property(self):
        norm = Account.from_dict(self.normal_account_dict['account'])
        self.assertEqual(norm.property('zimbraFeatureSignaturesEnabled'), True)
