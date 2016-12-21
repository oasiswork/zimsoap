#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Misc tool functions """

import pythonzimbra
import pythonzimbra.tools.xmlserializer

import re
import hmac
import hashlib
from xml.dom import minidom

re_zuuid = re.compile(r'[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}')


def is_zuuid(s):
    """ Is it a zimbraUUID ?

    example zimbra UUID : d78fd9c9-f000-440b-bce6-ea938d40fa2d
    """
    return re_zuuid.match(s)


def build_preauth_str(preauth_key, account_name, timestamp, expires,
                      admin=False):
    """ Builds the preauth string and hmac it, following the zimbra spec.

    Spec and examples are here http://wiki.zimbra.com/wiki/Preauth
    """
    if admin:
        s = '{0}|1|name|{1}|{2}'.format(account_name, expires, timestamp)
    else:
        s = '{0}|name|{1}|{2}'.format(account_name, expires, timestamp)

    return hmac.new(preauth_key.encode('utf-8'), s.encode('utf-8'),
                    hashlib.sha1).hexdigest()


def wrap_in_cdata(s):
    return "<![CDATA[{0}]]>".format(s)


def as_list(obj):
    if isinstance(obj, (list, tuple)):
        return obj
    else:
        return [obj]


def get_content(obj):
    """ Works arround (sometimes) non predictible results of pythonzimbra

    Sometime, the content of an XML tag is wrapped in {'_content': foo},
    sometime it is accessible directly.
    """
    if isinstance(obj, dict):
        return obj['_content']
    else:
        return obj


def auto_type(val):
    """ Get a XML response and tries to convert it to Python base object
    """
    try:
        s = str(val)
    except UnicodeEncodeError:
        # Some times, str() fails because of accents...
        s = val

    if isinstance(s, bool):
        return s
    elif s is None:
        return ''
    elif s == 'TRUE':
        return True
    elif s == 'FALSE':
        return False
    else:
        try:
            try:
                # telephone numbers may be wrongly interpretted as ints
                if s.startswith('+'):
                    return s
                else:
                    return int(s)
            except ValueError:
                return float(s)

        except ValueError:
            return s


def auto_untype(arg):
    """ The oposite of auto_type : takes a python base object and tries to
    convert it to XML typed string.
    """
    if arg is True:
        return 'TRUE'
    elif arg is False:
        return 'FALSE'
    else:
        return arg


def bool2strint(val):
    """ Convert a boolean to a '0' or '1' string to be used in requests
    """
    if val is True:
        return '1'
    elif val is False:
        return '0'
    else:
        raise ValueError('Expecting a boolean, this is a {}'.format(type(val)))


def xml_str_to_dict(s):
    """ Transforms an XML string it to python-zimbra dict format

    For format, see:
      https://github.com/Zimbra-Community/python-zimbra/blob/master/README.md

    :param: a string, containing XML
    :returns: a dict, with python-zimbra format
    """
    xml = minidom.parseString(s)
    return pythonzimbra.tools.xmlserializer.dom_to_dict(xml.firstChild)
