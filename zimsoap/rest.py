#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Zimbra REST clients

For some operations we can't do with SOAP API, such as admin preauth.
"""

import time
try:
    from urllib2 import HTTPCookieProcessor, build_opener, HTTPError
except ImportError:
    from urllib.request import HTTPCookieProcessor, build_opener, HTTPError

from six.moves import http_cookiejar, urllib

from zimsoap import utils


class RESTClient:

    class NoPreauthKeyProvided(Exception):
        pass

    class RESTBackendError(Exception):
        def __init__(self, e):
            self.parent = e
            self.msg = 'Zimbra issued HTTP error : '+e.msg
            Exception.__init__(self, self.msg)

    def __init__(self, server_host, server_port=None, preauth_key=None):
        if server_port:
            self.preauth_url = 'https://{0}:{1}/service/preauth?'.format(
                server_host, server_port)
        else:
            self.preauth_url = 'https://{0}/service/preauth?'.format(
                server_host)

        self.set_preauth_key(preauth_key)

    def set_preauth_key(self, preauth_key):
        self.preauth_key = preauth_key

    def get_preauth_token(self, account_name, expires=0):
        if not self.preauth_key:
            raise self.NoPreauthKeyProvided

        ts = int(time.time())*1000

        preauth_str = utils.build_preauth_str(self.preauth_key, account_name,
                                              ts, expires, admin=self.isadmin)

        args = urllib.parse.urlencode({
            'account': account_name,
            'by': 'name',
            'timestamp': ts,
            'expires': expires*1000,
            'admin': "1" if self.isadmin else "0",
            'preauth': preauth_str
        })

        cj = http_cookiejar.CookieJar()
        browser = build_opener(HTTPCookieProcessor(cj))

        try:
            url = browser.open(self.preauth_url+args)
            url.read()
            value = ""
            for cookie in cj:
                if cookie.name == self.TOKEN_COOKIE:
                    value = cookie.value
            url.close()
            browser.close()
            return value
        except HTTPError as e:
            raise self.RESTBackendError(e)


class AdminRESTClient(RESTClient):
    TOKEN_COOKIE = 'ZM_ADMIN_AUTH_TOKEN'

    def __init__(self, server_host, server_port=7071, preauth_key=None):
        self.isadmin = True
        RESTClient.__init__(
            self, server_host, server_port, preauth_key)


class AccountRESTClient(RESTClient):
    TOKEN_COOKIE = 'ZM_AUTH_TOKEN'

    def __init__(self, *args, **kwargs):
        self.isadmin = False
        RESTClient.__init__(self, *args, **kwargs)


class MailRESTClient(RESTClient):
    TOKEN_COOKIE = 'ZM_MAIL_AUTH_TOKEN'

    def __init__(self, *args, **kwargs):
        self.isadmin = False
        RESTClient.__init__(self, *args, **kwargs)
