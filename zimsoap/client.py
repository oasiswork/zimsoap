#!/usr/bin/env python
# -*- coding: utf-8 -*-


from os.path import dirname, abspath, join
import datetime

import pysimplesoap

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
        WSDL_PATH = abspath(join(dirname(dirname(abspath(__file__))),
                                 'share/zimbra.wsdl'))

        super(ZimbraAdminClient, self).__init__(wsdl=WSDL_PATH, *args, **kwargs)

        # Set service location as it cannot be mentioned in static wsdl
        self.services['ZimbraService']['ports']['ZimbraServicePort']['location'] = \
            "https://%s:%s/service/admin/soap" % (server_host, server_port)

        self._session = ZimbraAPISession(self)

    def login(self, admin_user, admin_password):
        self._session.login(admin_user, admin_password)
        self['context'] = self._session.get_context_header()


class ZimbraAPISession:
    def __init__(self, client):
        self.client = client
        self.authToken = None

    def login(self, username, password):
        """ Performrs the login agains zimbra:
             - performs an AuthRequest
             - prepare an authentification header with the received authtoken
               for subsequent requests.
        """
        response = self.client.AuthRequest(username, password)
        self.authToken = response[0]['authToken']
        lifetime = int(response[1]['lifetime'])
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


