#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Misc tools.

import pysimplesoap

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

        @returns a SimpleXMLElement iterable
    """
    return xml_response.children()[1].children()[0].children()


def extractSingleResponse(xml_response):
    return extractResponses(xml_response)[0]

def wrap_el(element):
    """Workaround a pysimplesoap bug, to push a first-level child of the
    request tag, we can't push it "as-is", so we wrap it inside some fake
    <l></l> tag.

    FIXME: should patch pysimplesoap instead

    @param element a SimpleXMLElement
    @returns       a SimpleXMLElement: the argument, wrapped in <l/>
    """

    wrapper = pysimplesoap.client.SimpleXMLElement('<l/>')
    wrapper.import_node(element)
    return wrapper
