#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Misc tool functions """

import pysimplesoap
import re
import hmac
import hashlib

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
        s = '{}|1|name|{}|{}'.format(account_name, expires, timestamp)
    else:
        s = '{}|name|{}|{}'.format(account_name, expires, timestamp)

    return hmac.new(preauth_key,s,hashlib.sha1).hexdigest()

def wrap_in_cdata(s):
    return "<![CDATA[{}]]>".format(s)

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
