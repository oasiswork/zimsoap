#!/usr/bin/env python
# -*- coding: utf-8 -*-


from os.path import dirname, abspath, join
import datetime

import pysimplesoap



class ZimbraAdminClient(pysimplesoap.client.SoapClient):
    """ Specialized Soap client to access zimbraAdmin webservice, handling auth.
    API ref is
    http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/zimbraAdmin/service-summary.html
    """
    def __init__(self, admin_user, admin_password, server_host, server_port='7071',
                 *args, **kwargs):
        WSDL_PATH = abspath(join(dirname(dirname(abspath(__file__))),
                                 'share/zimbra.wsdl'))

        super(ZimbraAdminClient, self ).__init__(wsdl=WSDL_PATH)

        # Set service location as it cannot be mentioned in static wsdl
        self.services['ZimbraService']['ports']['ZimbraServicePort']['location'] = \
            "https://%s:%s/service/admin/soap" % (server_host, server_port)

        self.authToken = None
        self._login(admin_user, admin_password,
                    *args, **kwargs)


    def _login(self, admin_user, admin_password):
        """ Performrs the login agains zimbra:
             - performs an AuthRequest
             - prepare an authentification header with the received authtoken
               for subsequent requests.
        """
        response = self.AuthRequest(admin_user, admin_password)
        self.authToken = response[0]['authToken']
        self.lifetime = response[1]['lifetime']

        # Prepare auth header, that will be stick to all subsequent request:
        context = pysimplesoap.client.SimpleXMLElement("<context/>")
        context['xmlns'] = "urn:zimbra"
        context.authToken = self.authToken
        context.authToken['xsi:type'] = "xsd:string"
        context.add_child('sessionId')
        context.sessionId['xsi:null'] = "1"

        self['context'] = context

    def is_logged_in(self):
        #TODO : session expiration
        return self.authToken != None


class ZimbraAPISession:
    def __init__(self, client):
        self.client = client
        self.authToken = None

    def login(self, username, password):
        response = self.client.AuthRequest(username, password)
        self.authToken = response[0]['authToken']
        lifetime = int(response[1]['lifetime'])
        self.end_date = (datetime.datetime.now() +
                             datetime.timedelta(0, lifetime))

    def is_logged_in(self):
        if not self.authToken:
            return False
        return self.end_date >= datetime.datetime.now()


