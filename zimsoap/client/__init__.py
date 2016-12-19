#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Zimbra SOAP client pythonic abstraction

core classes for SOAP clients, there are also REST clients here, but used only
for pre-authentification.
"""

import datetime
try:
    from urllib2 import HTTPError
except ImportError:
    from urllib.request import HTTPError

from six import text_type, binary_type
import pythonzimbra
import pythonzimbra.tools.auth
from pythonzimbra.communication import Communication

from zimsoap import zobjects
from zimsoap.exceptions import (
    ZimbraSoapServerError,
    ZimbraSoapUnexpectedResponse
)


class ZimbraAPISession:
    """Handle the login, the session expiration and the generation of the
       authentification header.
    """
    def __init__(self, client):
        self.client = client
        self.authToken = None

    def set_end_date(self, lifetime):
        """Computes and store an absolute end_date session according to the
        lifetime of the session"""
        self.end_date = (datetime.datetime.now() +
                         datetime.timedelta(0, lifetime))

    def login(self, username, password, namespace=None):
        """ Performs the login against zimbra
        (sends AuthRequest, receives AuthResponse).

        :param namespace: if specified, the namespace used for authetication
                         (if the client namespace is not suitable for
                         authentication).
        """

        if namespace is None:
            namespace = self.client.NAMESPACE

        data = self.client.request(
            'Auth',
            {
                'account': zobjects.admin.Account(name=username).to_selector(),
                'password': {'_content': password}
            },
            namespace)
        self.authToken = data['authToken']
        lifetime = int(data['lifetime'])

        self.authToken = str(self.authToken)
        self.set_end_date(lifetime)

    def import_session(self, auth_token):
        if not isinstance(auth_token, (binary_type, text_type)):
            raise TypeError('auth_token should be a string, not {0}'.format(
                type(auth_token)))
        self.authToken = auth_token

    def is_logged_in(self, force_check=False):
        if not self.authToken:
            return False

        # if it's logged-in by preauth, we can't know the exp. date for sure
        try:
            return self.end_date >= datetime.datetime.now()
        except AttributeError:
            return True

    def is_session_valid(self):
        try:
            self.client.request('Auth',
                                {'authToken': {'_content': self.authToken}})
            return True
        except ZimbraSoapServerError:
            return False


class ZimbraAbstractClient(object):
    """ Factorized abstract code for SOAP API access.

    Provides common ground for zimbraAdmin, zimbraAccount and zimbraMail.
    """
    def __init__(self, server_host, server_port, *args, **kwargs):
        loc = 'https://%s:%s/%s' % (server_host, server_port, self.LOCATION)
        self.com = Communication(loc)
        self._server_host = server_host
        self._server_port = server_port

        self._session = ZimbraAPISession(self)

    def request(self, name, content={}, namespace=None):
        """ Do a SOAP request and returns the result.

        Simple wrapper arround pythonzimbra functions
        :param name: ex: 'Auth' for performing an 'AuthRequest'
        :param content: a dict formatted pythonzimbra-style for request
        :param namespace: (optional), the namespace, if different from the
                          client's

        :returns: a dict with response
        """
        if not namespace:
            namespace = self.NAMESPACE

        req_name = name+'Request'
        resp_name = name+'Response'
        req = pythonzimbra.request_xml.RequestXml()
        resp = pythonzimbra.response_xml.ResponseXml()

        if self._session.is_logged_in():
            req.set_auth_token(self._session.authToken)

        req.add_request(req_name, content, namespace)
        try:
            self.com.send_request(req, resp)
        except HTTPError as e:
            if resp:
                raise ZimbraSoapServerError(e.req, e.resp)
            else:
                raise

        try:
            resp_content = resp.get_response()
            return resp_content[resp_name]
        except KeyError:
            if resp.is_fault():
                raise ZimbraSoapServerError(req, resp)
            raise ZimbraSoapUnexpectedResponse(
                req, resp, 'Cannot find {} in response "{}"'.format(
                    resp_name, resp.get_response()))

        return resp_content

    def request_single(self, name, content={}):
        """ Simple wrapper arround request to extract a single response

        :returns: the first tag in the response body
        """
        resp = self.request(name, content)

        # We stop on the first non-attribute (attributes are unicode/str)
        # If it's a list, we only return the first one.

        for i in resp.values():
            if type(i) == list:
                return i[0]
            elif type(i) == dict:
                return i

        return None

    def request_list(self, name, content={}):
        """ Simple wrapper arround request to extract a list of response

        :returns: the list of tags with same name or empty list
        """
        resp = self.request(name, content)

        # We stop on the first non-attribute (attributes are unicode/str)
        # If it's a list, we only return the first one.

        for i in resp.values():
            if type(i) == list:
                return i
            elif type(i) == dict:
                return [i]

        return []

    def login(self, user, password):
        self._session.login(user, password)

    def login_with_authToken(self, authToken, lifetime=None):
        self._session.import_session(authToken)
        if lifetime:
            self._session.set_end_date(int(lifetime))

    def get_logged_in_by(self, login, parent_zc, duration=0):
        """Use another client to get logged in via preauth mechanism by an
        already logged in admin.

        It required the domain of the admin user to have preAuthKey
        The preauth key cannot be created by API, do it with zmprov :
            zmprov gdpak <domain>
        """
        domain_name = zobjects.admin.Account(name=login).get_domain()
        preauth_key = parent_zc.get_domain(domain_name)['zimbraPreAuthKey']

        rc = self.REST_PREAUTH(
            self._server_host, parent_zc._server_port, preauth_key=preauth_key)

        authToken = rc.get_preauth_token(login)

        self.login_with_authToken(authToken)

    def delegated_login(self, login, admin_zc, duration=0):
        """Use another client to get logged in via delegated_auth mechanism by an
        already logged in admin.

        :param login: the user login (or email) you want to log as
        :param admin_zc: An already logged-in admin client
        :type admin_zc: ZimbraAdminClient
        """
        # a duration of zero is interpretted literaly by the API...
        selector = zobjects.admin.Account(name=login).to_selector()
        delegate_args = {'account': selector}
        if duration:
            delegate_args['duration': duration]
        resp = admin_zc.request('DelegateAuth', delegate_args)

        lifetime = resp['lifetime']
        authToken = resp['authToken']

        self.login_account = login
        self.login_with_authToken(authToken, lifetime)

    def is_session_valid(self):
        # some classes may need to overload it
        return self._session.is_session_valid()

    def get_host(self):
        return self._server_host
