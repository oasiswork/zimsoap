#!/usr/bin/env python
# -*- coding: utf-8 -*-
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

def build_preauth_str(preauth_key, account_name, timestamp, expires, admin=False):
    """ Builds the preauthentification string and hmac it, following the zimbra spec.

    spec and examples are here http://wiki.zimbra.com/wiki/Preauth
    """
    if admin:
        s = '{0}|1|name|{1}|{2}'.format(account_name, expires, timestamp)
    else:
        s = '{0}|name|{1}|{2}'.format(account_name, expires, timestamp)

    return hmac.new(preauth_key,s,hashlib.sha1).hexdigest()

def wrap_in_cdata(s):
    return "<![CDATA[{0}]]>".format(s)

def auto_type(s):
    """ Get a XML response and tries to convert it to Python base object
    """
    if s == 'TRUE':
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
    if arg == True:
        return 'TRUE'
    elif arg == False:
        return 'FALSE'
    else:
        return arg

def xml_str_to_dict(s):
    """ Transforms an XML string it to python-zimbra dict format

    For format, see:
      https://github.com/Zimbra-Community/python-zimbra/blob/master/README.md

    :param: a string, containing XML
    :returns: a dict, with python-zimbra format
    """
    xml = minidom.parseString(s)
    return pythonzimbra.tools.xmlserializer.dom_to_dict(xml.firstChild)
