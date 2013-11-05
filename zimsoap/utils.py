#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Misc tools.


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
    return extractResponses(xml_response)[0]

def wrap_el(element):
    """Workaround a pysimplesoap bug, to push a first-level child of the
    request tag, we can't push it "as-is", so we wrap it inside some fake
    <l></l> tag.

    FIXME: should patch pysimplesoap instead. See
           http://code.google.com/p/pysimplesoap/issues/detail?id=89

    @param element a SimpleXMLElement
    @returns       a SimpleXMLElement: the argument, wrapped in <l/>
    """

    wrapper = pysimplesoap.client.SimpleXMLElement('<l/>')
    if type(element) in (list, tuple):
        for i in element:
            wrapper.import_node(i)
    else:
        wrapper.import_node(element)

    return wrapper


re_zuuid = re.compile(r'[0-9a-f]{8}-([0-9a-f]{4}-){3}[0-9a-f]{12}')
def is_zuuid(s):
    """ Is it a zimbraUUID ?

    example zimbra UUID : d78fd9c9-f000-440b-bce6-ea938d40fa2d
    """
    return re_zuuid.match(s)

def build_preauth_str(preauth_key, account_name, timestamp, expires):
    s = '{}|name|{}|{}'.format(account_name, expires, timestamp)
    return hmac.new(preauth_key,s,hashlib.sha1).hexdigest()
