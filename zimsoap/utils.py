#!/usr/bin/env python
# -*- coding: utf-8 -*-
""" Misc tool functions """

import pysimplesoap
import re
import hmac
import hashlib

def extractResponses(xml_response):
    """ A raw message is like:
        <?xml version="1.0" encoding="utf-16"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Header>
            </soap:Header>
            <soap:Body>
                <MyResponseEnvelope xmlns="urn:zimbraAdmin">
                    <ResponseElement1>...</ResponseElement1>
                    <ResponseElement2>...</ResponseElement2>
                </GetAllDomainsResponse>
            </soap:Body>
        </soap:Envelope>

        this functions extracts only the ResponseElementN elements as an iterable

        @returns a SimpleXMLElement iterable or an empty list
    """
    responses = xml_response.children()[1].children()[0].children()
    # Returns an emptylist rather to "None"
    if responses:
        return [i for i in responses]
    else:
        return []



def extractSingleResponse(xml_response):
    """ Same as extractResponses but returns the first response instead of a list
    """
    return extractResponses(xml_response)[0]

def extractResponseTag(xml_response):
    """ A raw message is like:
        <?xml version="1.0" encoding="utf-16"?>
        <soap:Envelope xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
            <soap:Header>
            </soap:Header>
            <soap:Body>
                <MyResponseEnvelope xmlns="urn:zimbraAdmin">
                ...
                </GetAllDomainsResponse>
            </soap:Body>
        </soap:Envelope>

        this functions extracts the MyResponseEnvelope tag.

        @returns a SimpleXMLElement, which name is likely to be "SomethingResponse"
    """
    return xml_response.children()[1].children()[0]

def wrap_el(element):
    """Workaround a pysimplesoap bug, to push a first-level child of the
    request tag, we can't push it "as-is", so we wrap it inside some fake
    <l></l> tag.

    FIXME: should patch pysimplesoap instead. See
           http://code.google.com/p/pysimplesoap/issues/detail?id=89

    @param element a SimpleXMLElement or a list of SimpleXMLElement
    @returns       a SimpleXMLElement: the argument(s), wrapped in <l/>
    """
    wrapper = pysimplesoap.client.SimpleXMLElement('<l/>')

    if not type(element) in (list, tuple):
        element = [element]

    for i in element:
        if not isinstance(i, pysimplesoap.client.SimpleXMLElement):
            raise TypeError(
                'expecting a SimpleXMLElement, not {}'.format(type(i)))

        wrapper.import_node(i)

    return wrapper


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
