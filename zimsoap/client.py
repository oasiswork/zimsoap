#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# This client has two usages:
#
#   - Fire SOAP methods (they are "CamelCameNames()" and end with 'Request'):
#     they bind directly to sending the same-name message to the SOAP
#     server. They return XML.
#
#   - Fire high-level methods (they are "pythonic_method_names()"), they return
#     Python objects/list (see zobjects submodule for zimbra-specific Classes).
#

from os.path import dirname, abspath, join
import datetime

import pysimplesoap

import utils
import zobjects

class ShouldAuthenticateFirst(Exception):
    """ Error fired when an operation requiring auth is intented before the auth
    is done.
    """
    pass

class ZimbraAdminClient(pysimplesoap.client.SoapClient):
    """ Specialized Soap client to access zimbraAdmin webservice, handling auth.

    API ref is
    http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/zimbraAdmin/service-summary.html
    """
    def __init__(self, server_host, server_port='7071',
                 *args, **kwargs):
        loc = "https://%s:%s/service/admin/soap" % (server_host, server_port)
        super(ZimbraAdminClient, self).__init__(
            location = loc,
            action = loc,
            namespace = 'urn:zimbraAdmin',
            *args, **kwargs)

        self._session = ZimbraAPISession(self)

    def login(self, admin_user, admin_password):
        self._session.login(admin_user, admin_password)
        self['context'] = self._session.get_context_header()

    def get_all_domains(self):
        obj_domains = []
        xml_doms = utils.extractResponses(self.GetAllDomainsRequest())
        return [zobjects.Domain.from_xml(d) for d in xml_doms]

    def get_mailbox_stats(self):
        """ Get global stats about mailboxes

        Parses <stats numMboxes="6" totalSize="141077"/>

        @returns dict with stats
        """
        resp = utils.extractSingleResponse(self.GetMailboxStatsRequest())
        ret = {}
        for k,v in resp.attributes().items():
            ret[k] = int(v)

        return ret

class ZimbraAPISession:
    """Handle the login, the session expiration and the generation of the
       authentification header.
    """
    def __init__(self, client):
        self.client = client
        self.authToken = None

    def login(self, username, password):
        """ Performs the login agains zimbra
        (sends AuthRequest, receives AuthResponse).
        """
        response = self.client.AuthRequest(name=username, password=password)
        self.authToken, lifetime = utils.extractResponses(response)
        lifetime = int(lifetime)
        self.authToken = str(self.authToken)
        self.end_date = (datetime.datetime.now() +
                         datetime.timedelta(0, lifetime))

    def get_context_header(self):
        """ Builds the XML <context> element to be tied to SOAP requests. It
        contains the authentication string (authToken).

        @return the context as a pysimplesoap.client.SimpleXMLElement
        """

        if not self.is_logged_in():
            raise ShouldAuthenticateFirst

        context = pysimplesoap.client.SimpleXMLElement("<context/>")
        context['xmlns'] = "urn:zimbra"
        context.authToken = self.authToken
        context.authToken['xsi:type'] = "xsd:string"
        context.add_child('sessionId')
        context.sessionId['xsi:null'] = "1"

        return context

    def is_logged_in(self):
        if not self.authToken:
            return False
        return self.end_date >= datetime.datetime.now()


