#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Unittests for zimsoap.utils """

import unittest

import zimsoap
from zimsoap import utils

import pythonzimbra

from pythonzimbra.communication import Communication


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


    def test_auto_type_int(self):
        self.assertIsInstance(utils.auto_type('42'), int)

    def test_auto_type_float(self):
        self.assertIsInstance(utils.auto_type('4.2'), float)

    def test_auto_type_str(self):
        self.assertIsInstance(utils.auto_type('forty-two'), str)

    def test_auto_type_bool(self):
        self.assertIsInstance(utils.auto_type('TRUE'), bool)
        self.assertIsInstance(utils.auto_type('FALSE'), bool)

    def test_auto_type_none(self):
        self.assertEqual(utils.auto_type(None), '')

    def test_auto_untype_bool(self):
        self.assertEqual(utils.auto_untype(True), 'TRUE')
        self.assertEqual(utils.auto_untype(False), 'FALSE')

    def test_auto_untype_any(self):
        self.assertEqual(utils.auto_untype('foo'), 'foo')


    def test_xml_str_to_dict(self):
        xml = (
            '<a foo="bar" faa="bor"></a>',
            '<a>text</a>',
            '<a><sub>a</sub></a>',
            '<a><sub>foo</sub><sub>bar</sub></a>',
        )

        dicts = (
            {'a': {'foo': 'bar', 'faa': 'bor'}},
            {'a': {'_content': 'text'}},
            {'a': {'sub': {'_content': 'a'}}},
            {'a': {'sub': [{'_content': 'foo'}, {'_content': 'bar'}]}},

        )
        for i in range(len(xml)):
            self.assertEqual(
                utils.xml_str_to_dict(xml[i]),
                dicts[i])
