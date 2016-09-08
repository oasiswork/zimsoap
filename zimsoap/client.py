#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Zimbra SOAP client pythonic abstraction

core classes for SOAP clients, there are also REST clients here, but used only
for pre-authentification.
"""

import datetime
try:
    from urllib2 import HTTPCookieProcessor, build_opener, HTTPError
except ImportError:
    from urllib.request import HTTPCookieProcessor, build_opener, HTTPError
import time
import re
import warnings

from six.moves import http_cookiejar, urllib
from six import text_type, binary_type
import pythonzimbra
import pythonzimbra.tools.auth
from pythonzimbra.communication import Communication

from zimsoap import utils
from zimsoap import zobjects


class RESTClient:
    """ Abstract Classe, RESTClient defines a REST client for some operations we
    can't do with SOAP API, such as admin preauth.
    """
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
        RESTClient.__init__(self, server_host, server_port, preauth_key)


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


class ZimSOAPException(Exception):
    pass


class ShouldAuthenticateFirst(ZimSOAPException):
    """ Error fired when an operation requiring auth is intented before the auth
    is done.
    """
    pass


class DomainHasNoPreAuthKey(ZimSOAPException):
    """ Error fired when the server has no preauth key
    """
    def __init__(self, domain):
        # Call the base class constructor with the parameters it needs
        self.msg = '"{0}" has no preauth key, make one first, see {1}'.format(
            domain.name,
            'http://wiki.zimbra.com/wiki/Preauth'
            '#Preparing_a_domain_for_preauth'
            )
        Exception.__init__(self)


class ZimbraSoapServerError(ZimSOAPException):
    r_soap_text = re.compile(r'<soap:Text>(.*)</soap:Text>')

    def __init__(self, request, response):
        self.request = request
        self.response = response

        fault = response.get_response()['Fault']
        self.msg = fault['Reason']['Text']
        self.code = fault['Detail']['Error']['Code']
        self.trace_url = fault['Detail']['Error']['Trace']

    def __str__(self):
        return '{0}: {1}'.format(
            self.code, self.msg)


class ZimbraSoapUnexpectedResponse(ZimSOAPException):
    def __init__(self, request, response, msg=''):
        self.request = request
        self.response = response
        self.msg = msg

    def __str__(self):
        if self.msg:
            return self.msg
        else:
            return 'Unexpected Response from Zimbra Server'


class ZimbraAbstractClient(object):
    """ Factorized abstract code for SOAP API access.

    Provides common ground for zimbraAdmin and zimbraAccount.
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
            if 'Fault' in resp_content:
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
        domain_name = zobjects.Account(name=login).get_domain()
        preauth_key = parent_zc.get_domain(domain_name)['zimbraPreAuthKey']

        rc = self.REST_PREAUTH(
            self._server_host, parent_zc._server_port, preauth_key=preauth_key)

        authToken = rc.get_preauth_token(login)

        self.login_with_authToken(authToken)

    def delegated_login(self, login, admin_zc, duration=0):
        """Use another client to get logged in via delegated_auth mechanism by an
        already logged in admin.

        :param admin_zc: An already logged-in admin client
        :type admin_zc: ZimbraAdminClient
        :param login: the user login (or email) you want to log as
        """
        # a duration of zero is interpretted literaly by the API...
        selector = zobjects.Account(name=login).to_selector()
        delegate_args = {'account': selector}
        if duration:
            delegate_args['duration': duration]
        resp = admin_zc.request('DelegateAuth', delegate_args)

        lifetime = resp['lifetime']
        authToken = resp['authToken']

        self.login_with_authToken(authToken, lifetime)

    def is_session_valid(self):
        # some classes may need to overload it
        return self._session.is_session_valid()

    def get_host(self):
        return self._server_host


class ZimbraAccountClient(ZimbraAbstractClient):
    """ Specialized Soap client to access zimbraAccount webservice.

    API ref is
    http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/zimbraAccount/service-summary.html
    """
    NAMESPACE = 'urn:zimbraAccount'
    LOCATION = 'service/soap'
    REST_PREAUTH = AccountRESTClient

    def __init__(self, server_host, server_port='443', *args, **kwargs):
        super(ZimbraAccountClient, self).__init__(
            server_host, server_port,
            *args, **kwargs)

    def create_signature(self, name, content, contenttype="text/html"):
        """
        :param:  name        verbose name of the signature
        :param:  content     content of the signature, in html or plain-text
        :param:  contenttype can be "text/html" (default) or "text/plain"
        :returns: a zobjects.Signature object
        """
        s = zobjects.Signature(name=name)
        s.set_content(content, contenttype)

        resp = self.request('CreateSignature', {'signature': s.to_creator()})
        return zobjects.Signature.from_dict(resp['signature'])

    def get_signatures(self):
        """ Get all signatures for the current user

        :returns: a list of zobjects.Signature
        """
        signatures = self.request_list('GetSignatures')

        return [zobjects.Signature.from_dict(i) for i in signatures]

    def get_signature(self, signature):
        """Retrieve one signature, discriminated by name or id.

        Note that signature name is not case sensitive.

        :param: a zobjects.Signature describing the signature
               like "Signature(name='my-sig')"

        :returns: a zobjects.Signature object, filled with the signature if no
                 signature is matching, returns None.
        """
        resp = self.request_list('GetSignatures')

        # GetSignature does not allow to filter the results, so we do it by
        # hand...
        if resp and (len(resp) > 0):
            for sig_dict in resp:
                sig = zobjects.Signature.from_dict(sig_dict)
                if hasattr(signature, 'id'):
                    its_this_one = (sig.id == signature.id)
                elif hasattr(signature, 'name'):
                    its_this_one = (sig.name.upper() == signature.name.upper())
                else:
                    raise ValueError('should mention one of id,name')
                if its_this_one:
                    return sig
        else:
            return None

    def delete_signature(self, signature):
        """ Delete a signature by name or id

        :param: signature a Signature object with name or id defined
        """
        self.request('DeleteSignature', {'signature': signature.to_selector()})

    def modify_signature(self, signature):
        """ Modify an existing signature

        Can modify the content, contenttype and name. An unset attribute will
        not delete the attribute but leave it untouched.
        :param: signature a zobject.Signature object, with modified
                         content/contentype/name, the id should be present and
                          valid, the name does not allows to identify the
                         signature for that operation.
        """
        # if no content is specified, just use a selector (id/name)
        dic = signature.to_creator(for_modify=True)

        self.request('ModifySignature', {'signature': dic})

    def get_preferences(self):
        """ Gets all the preferences of the current user

        :returns: a dict presenting the preferences by name, values are
                 typed to str/bool/int/float regarding their content.
        """
        pref_list = self.request('GetPrefs')['pref']

        out = {}
        for pref in pref_list:
            out[pref['name']] = utils.auto_type(pref['_content'])

        return out

    def get_preference(self, pref_name):
        """ Gets a single named preference

        :returns: the value, typed to str/bool/int/float regarding its content.
        """
        resp = self.request_single('GetPrefs', {'pref': {'name': pref_name}})
        return utils.auto_type(resp['_content'])

    def get_identities(self):
        """ Get all the identities of the user, as a list

        :returns: list of zobjects.Identity
        """
        resp = self.request('GetIdentities')

        if 'identity' in resp:
            identities = resp['identity']
            if type(identities) != list:
                identities = [identities]

            return [zobjects.Identity.from_dict(i) for i in identities]
        else:
            return []

    def modify_identity(self, identity):
        """ Modify some attributes of an identity or its name.

        :param: identity a zobjects.Identity with `id` set (mandatory). Also
               set items you want to modify/set and/or the `name` attribute to
               rename the identity.
        """
        self.request('ModifyIdentity', {'identity': identity.to_creator()})

    # Whitelists and Blacklists

    def get_white_black_lists(self):
        return self.request('GetWhiteBlackList')

    def add_to_blacklist(self, values):
        param = {'blackList': {'addr': []}}
        for value in values:
            param['blackList']['addr'].append({'op': '+', '_content': value})

        self.request('ModifyWhiteBlackList', param)

    def remove_from_blacklist(self, values):
        param = {'blackList': {'addr': []}}
        for value in values:
            param['blackList']['addr'].append({'op': '-', '_content': value})

        self.request('ModifyWhiteBlackList', param)

    def add_to_whitelist(self, values):
        param = {'whiteList': {'addr': []}}
        for value in values:
            param['whiteList']['addr'].append({'op': '+', '_content': value})

        self.request('ModifyWhiteBlackList', param)

    def remove_from_whitelist(self, values):
        param = {'whiteList': {'addr': []}}
        for value in values:
            param['whiteList']['addr'].append({'op': '-', '_content': value})

        self.request('ModifyWhiteBlackList', param)


class ZimbraAdminClient(ZimbraAbstractClient):
    """ Specialized Soap client to access zimbraAdmin webservice, handling auth.

    API ref is
    http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/zimbraAdmin/service-summary.html
    """
    NAMESPACE = 'urn:zimbraAdmin'
    LOCATION = 'service/admin/soap'
    REST_PREAUTH = AdminRESTClient

    def __init__(self, server_host, server_port='7071',
                 *args, **kwargs):
        super(ZimbraAdminClient, self).__init__(
            server_host, server_port,
            *args, **kwargs)

    def get_quota_usage(self, domain=None, all_servers=None,
                        limit=None, offset=None, sort_by=None,
                        sort_ascending=None, refresh=None):
        content = {}
        if domain:
            content['domain'] = domain
        if all_servers:
            content['allServers'] = all_servers
        if limit:
            content['limit'] = limit
        if sort_by:
            content['sortBy'] = sort_by
        if sort_ascending:
            content['sortAscending'] = sort_ascending
        if refresh:
            content['refresh'] = refresh

        resp = self.request_list('GetQuotaUsage', content)

        return resp

    def get_all_config(self):
        resp = self.request_list('GetAllConfig')
        config = {}
        for attr in resp:
            # If there is multiple attributes with the same name
            if attr['n'] in config:
                if isinstance(config[attr['n']], str):
                    config[attr['n']] = [config[attr['n']], attr['_content']]
                else:
                    config[attr['n']].append(attr['_content'])
            else:
                config[attr['n']] = attr['_content']
        return config

    def get_config(self, attr):
        resp = self.request_list('GetConfig', {'a': {'n': attr}})
        if len(resp) > 1:
            config = {attr: []}
            for a in resp:
                config[attr].append(a['_content'])
        elif len(resp) == 1:
            config = {attr: resp[0]['_content']}
        else:
            raise KeyError('{} not found'.format(attr))
        return config

    def modify_config(self, attr, value):
        self.request('ModifyConfig', {
            'a': {
                'n': attr,
                '_content': value
            }})
        if attr[0] == '-' or attr[0] == '+':
            attr = attr[1::]
        return self.get_config(attr)

    def _get_or_fetch_id(self, zobj, fetch_func):
        """ Returns the ID of a Zobject wether it's already known or not

        If zobj.id is not known (frequent if zobj is a selector), fetches first
        the object and then returns its ID.

        :type zobj:       a zobject subclass
        :type fetch_func: the function to fetch the zobj from server if its id
                          is undefined.
        :returns:         the object id
        """

        try:
            return zobj.id
        except AttributeError:
            try:
                return fetch_func(zobj).id
            except AttributeError:
                raise ValueError('Unqualified Resource')

    def get_all_domains(self):
        resp = self.request_list('GetAllDomains')
        return [zobjects.Domain.from_dict(d) for d in resp]

    def get_all_accounts(self, domain=None, server=None,
                         include_system_accounts=False,
                         include_admin_accounts=True,
                         include_virtual_accounts=True):
        selectors = {}
        if domain:
            selectors['domain'] = domain.to_selector()
        if server:
            selectors['server'] = server.to_selector()

        dict_accounts = self.request_list('GetAllAccounts', selectors)

        accounts = []
        for i in dict_accounts:
            account = zobjects.Account.from_dict(i)

            if not (
                not include_system_accounts and account.is_system() or
                not include_admin_accounts and account.is_admin() or
                not include_virtual_accounts and account.is_virtual()
            ):
                accounts.append(account)

        return accounts

    # Calendar resources

    def get_all_calendar_resources(self, domain=None, server=None,):
        selectors = {}
        if domain:
            selectors['domain'] = domain.to_selector()
        if server:
            selectors['server'] = server.to_selector()

        dict_calres = self.request_list('GetAllCalendarResources', selectors)

        resources = []
        for i in dict_calres:
            calres = zobjects.CalendarResource.from_dict(i)
            resources.append(calres)

        return resources

    def get_calendar_resource(self, cal_resource):
        """ Fetches an calendar resource with all its attributes.

        :param account: a CalendarResource, with either id or
                        name attribute set.
        :returns: a CalendarResource object, filled.
        """
        selector = cal_resource.to_selector()
        resp = self.request_single('GetCalendarResource',
                                   {'calresource': selector})
        return zobjects.CalendarResource.from_dict(resp)

    def create_calendar_resource(self, name, password=None, attrs={}):
        """
        :param: attrs a dict of attributes, must specify the displayName and
                     zimbraCalResType
        """
        args = {
            'name': name,
            'a': [{'n': k, '_content': v} for k, v in attrs.items()]
            }
        if password:
            args['password'] = password
        resp = self.request_single('CreateCalendarResource', args)
        return zobjects.CalendarResource.from_dict(resp)

    def delete_calendar_resource(self, calresource):
        self.request('DeleteCalendarResource', {
            'id': self._get_or_fetch_id(calresource,
                                        self.get_calendar_resource),
        })

    def modify_calendar_resource(self, calres, attrs):
        """
        :param calres: a zobjects.CalendarResource
        :param attrs:    a dictionary of attributes to set ({key:value,...})
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        self.request('ModifyCalendarResource', {
            'id': self._get_or_fetch_id(
                calres, self.get_calendar_resource),
            'a': attrs
        })

    def rename_calendar_resource(self, r_description, new_r_name):
        """
        :param r_description : a CalendarResource specifying either :
                   - id:   the ressource ID
                   - r_description: the name of the ressource
        :param new_r_name: new name of the list
        :return: a zobjects.CalendarResource
        """
        resp = self.request('RenameCalendarResource', {
            'id': self._get_or_fetch_id(r_description,
                                        self.get_calendar_resource),
            'newName': new_r_name
        })

        return zobjects.CalendarResource.from_dict(resp['calresource'])

    # Mailbox stats

    def get_mailbox_stats(self):
        """ Get global stats about mailboxes

        Parses <stats numMboxes="6" totalSize="141077"/>

        :returns: dict with stats
        """
        resp = self.request_single('GetMailboxStats')
        ret = {}
        for k, v in resp.items():
            ret[k] = int(v)

        return ret

    def count_account(self, domain):
        """ Count the number of accounts for a given domain, sorted by cos

        :returns: a list of pairs <ClassOfService object>,count
        """
        selector = domain.to_selector()
        cos_list = self.request_list('CountAccount', {'domain': selector})
        ret = []

        for i in cos_list:
            count = int(i['_content'])
            ret.append((zobjects.ClassOfService.from_dict(i),  count))

        return list(ret)

    def get_all_mailboxes(self):
        resp = self.request_list('GetAllMailboxes')

        return [zobjects.Mailbox.from_dict(i) for i in resp]

    def get_account_mailbox(self, account_id):
        """ Returns a Mailbox corresponding to an account. Usefull to get the
        size (attribute 's'), and the mailbox ID, returns nothing appart from
        that.
        """
        selector = zobjects.Mailbox(id=account_id).to_selector()
        resp = self.request_single('GetMailbox', {'mbox': selector})

        return zobjects.Mailbox.from_dict(resp)

    def get_account_cos(self, account):
        """ Fetch the cos for a given account

        Quite different from the original request which returns COS + various
        URL + COS + zimbraMailHost... But all other informations are accessible
        through get_account.

        :type account: zobjects.Account
        :rtype: zobjects.COS
        """
        resp = self.request(
            'GetAccountInfo', {'account': account.to_selector()})
        return zobjects.COS.from_dict(resp['cos'])

    def create_domain(self, name):
        """
        :param name: A string, NOT a zObject
        :return: a zobjects.Domain
        """
        args = {'name': name}
        resp = self.request_single('CreateDomain', args)

        return zobjects.Domain.from_dict(resp)

    def delete_domain(self, domain):
        self.request('DeleteDomain', {
            'id': self._get_or_fetch_id(domain, self.get_domain)
        })

    def delete_domain_forced(self, domain):
        # Remove aliases and accounts
        # we take all accounts because there might be an alias
        # for an account of an other domain
        accounts = self.get_all_accounts()
        for a in accounts:
            if 'zimbraMailAlias' in a._a_tags:
                aliases = a._a_tags['zimbraMailAlias']
                if isinstance(aliases, list):
                    for alias in aliases:
                        if alias.split('@')[1] == domain.name:
                            self.remove_account_alias(a, alias)
                else:
                    if aliases.split('@')[1] == domain.name:
                        self.remove_account_alias(a, aliases)
            if a.name.split('@')[1] == domain.name:
                self.delete_account(a)

        # Remove resources
        resources = self.get_all_calendar_resources(domain=domain)
        for r in resources:
            self.delete_calendar_resource(r)

        # Remove distribution lists
        dls = self.get_all_distribution_lists(domain)
        for dl in dls:
            self.delete_distribution_list(dl)

        self.request('DeleteDomain', {
            'id': self._get_or_fetch_id(domain, self.get_domain)
        })

    def get_domain(self, domain):
        selector = domain.to_selector()
        resp = self.request_single('GetDomain', {'domain': selector})
        return zobjects.Domain.from_dict(resp)

    def modify_domain(self, domain, attrs):
        """
        :type domain: a zobjects.Domain
        :param attrs: attributes to modify
        :type attrs dict
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        self.request('ModifyDomain', {
            'id': self._get_or_fetch_id(domain, self.get_domain),
            'a': attrs
        })

    def add_distribution_list_alias(self, distribution_list, alias):
        """
        :param distribution_list:  a distribution list object to be used as
         a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('AddDistributionListAlias', {
            'id': self._get_or_fetch_id(
                distribution_list, self.get_distribution_list
                ),
            'alias': alias,
        })

    def remove_distribution_list_alias(self, distribution_list, alias):
        """
        :param distribution_list:  an distribution list object to be used as
        a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('RemoveDistributionListAlias', {
            'id': self._get_or_fetch_id(
                distribution_list, self.get_distribution_list
            ),
            'alias': alias,
        })

    def get_all_distribution_lists(self, domain=None):
        if domain:
            selectors = {'domain': domain.to_selector()}
        else:
            selectors = {}

        got = self.request_list('GetAllDistributionLists', selectors)
        return [zobjects.DistributionList.from_dict(i) for i in got]

    def get_distribution_list(self, dl_description):
        """
        :param:   dl_description : a DistributionList specifying either :
                   - id:   the account_id
                   - name: the name of the list
        :returns: the DistributionList
        """
        selector = dl_description.to_selector()

        resp = self.request_single('GetDistributionList', {'dl': selector})
        dl = zobjects.DistributionList.from_dict(resp)
        return dl

    def create_distribution_list(self, name, dynamic=0):
        """

        :param name: A string, NOT a zObject
        :param dynamic:
        :return: a zobjects.DistributionList
        """
        args = {'name': name, 'dynamic': str(dynamic)}
        resp = self.request_single('CreateDistributionList', args)

        return zobjects.DistributionList.from_dict(resp)

    def modify_distribution_list(self, dl_description, attrs):
        """
        :param dl_description : a DistributionList specifying either :
                   - id:   the dl_list_id
                   - dl_description: the name of the list
        :param attrs  : a dictionary of attributes to set ({key:value,...})
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        self.request('ModifyDistributionList', {
            'id': self._get_or_fetch_id(dl_description,
                                        self.get_distribution_list),
            'a': attrs
        })

    def rename_distribution_list(self, dl_description, new_dl_name):
        """
        :param dl_description : a DistributionList specifying either :
                   - id:   the dl_list_id
                   - dl_description: the name of the list
        :param new_dl_name: new name of the list
        :return: a zobjects.DistributionList
        """
        resp = self.request('RenameDistributionList', {
            'id': self._get_or_fetch_id(dl_description,
                                        self.get_distribution_list),
            'newName': new_dl_name
        })

        return zobjects.DistributionList.from_dict(resp['dl'])

    def delete_distribution_list(self, dl):
        self.request('DeleteDistributionList', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list)
        })

    def add_distribution_list_member(self, distribution_list, members):
        """ Adds members to the distribution list

        :type distribution_list: zobjects.DistributionList
        :param members:          list of email addresses you want to add
        :type members:           list of str
        """
        members = [{'_content': v} for v in members]
        resp = self.request_single('AddDistributionListMember', {
            'id': self._get_or_fetch_id(distribution_list,
                                        self.get_distribution_list),
            'dlm': members
        })
        return resp

    def remove_distribution_list_member(self, distribution_list, members):
        """ Removes members from the distribution list

        :type distribution_list: zobjects.DistributionList
        :param members:          list of email addresses you want to remove
        :type members:           list of str
        """
        members = [{'_content': v} for v in members]
        resp = self.request_single('RemoveDistributionListMember', {
            'id': self._get_or_fetch_id(distribution_list,
                                        self.get_distribution_list),
            'dlm': members
        })
        return resp

    def get_account(self, account):
        """ Fetches an account with all its attributes.

        :param account: an account object, with either id or name attribute set
        :returns: a zobjects.Account object, filled.
        """
        selector = account.to_selector()
        resp = self.request_single('GetAccount', {'account': selector})
        return zobjects.Account.from_dict(resp)

    def rename_account(self, account, new_name):
        """ Rename an account.

        :param account: a zobjects.Account
        :param new_name: a string of new account name
        """
        self.request('RenameAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'newName': new_name
        })

    def modify_account(self, account, attrs):
        """
        :param account: a zobjects.Account
        :param attrs  : a dictionary of attributes to set ({key:value,...})
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        self.request('ModifyAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'a': attrs
        })

    def set_password(self, account, password):
        """
        :param account: a zobjects.Account
        :param password: new password to set
        """
        self.request('SetPassword', {
            'id': account.id,
            'newPassword': password
        })

    def create_account(self, email, password=None, attrs={}):
        """
        :param email:    Full email with domain eg: login@domain.com
        :param password: Password for local auth
        :param attrs:    a dictionary of attributes to set ({key:value,...})
        :returns:        the created zobjects.Account
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]

        params = {'name': email, 'a': attrs}

        if password:
            params['password'] = password

        resp = self.request_single('CreateAccount', params)

        return zobjects.Account.from_dict(resp)

    def delete_account(self, account):
        """
        :param account: an account object to be used as a selector
        """
        self.request('DeleteAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
        })

    def add_account_alias(self, account, alias):
        """
        :param account:  an account object to be used as a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('AddAccountAlias', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'alias': alias,
        })

    def remove_account_alias(self, account, alias):
        """
        :param account:  an account object to be used as a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('RemoveAccountAlias', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'alias': alias,
        })

    def mk_auth_token(self, account, admin=False, duration=0):
        """ Builds an authentification token, using preauth mechanism.

        See http://wiki.zimbra.com/wiki/Preauth

        :param duration: in seconds defaults to 0, which means "use account
               default"

        :param account: an account object to be used as a selector
        :returns:       the auth string
        """
        domain = account.get_domain()
        try:
            preauth_key = self.get_domain(domain)['zimbraPreAuthKey']
        except KeyError:
            raise DomainHasNoPreAuthKey(domain)
        timestamp = int(time.time())*1000
        expires = duration*1000
        return utils.build_preauth_str(preauth_key, account.name, timestamp,
                                       expires, admin)

    def delegate_auth(self, account):
        """ Uses the DelegateAuthRequest to provide a ZimbraAccountClient
        already logged with the provided account.

        It's the mechanism used with the "view email" button in admin console.
        """
        warnings.warn("delegate_auth() on parent client is deprecated,"
                      " use delegated_login() on child client instead",
                      DeprecationWarning)
        selector = account.to_selector()
        resp = self.request('DelegateAuth', {'account': selector})

        lifetime = resp['lifetime']
        authToken = resp['authToken']

        zc = ZimbraAccountClient(self._server_host)
        zc.login_with_authToken(authToken, lifetime)
        return zc

    def get_account_authToken(self, account=None, account_name=''):
        """ Use the DelegateAuthRequest to provide a token and his lifetime
        for the provided account.

        If account is provided we use it,
        else we retreive the account from the provided account_name.
        """
        if account is None:
            account = self.get_account(zobjects.Account(name=account_name))
        selector = account.to_selector()

        resp = self.request('DelegateAuth', {'account': selector})

        authToken = resp['authToken']
        lifetime = int(resp['lifetime'])

        return authToken, lifetime

    def delegated_login(self, *args, **kwargs):
        raise NotImplementedError(
            'zimbraAdmin do not support to get logged-in by delegated auth')

    def search_directory(self, **kwargs):
        """
        SearchAccount is deprecated, using SearchDirectory

        :param query: Query string - should be an LDAP-style filter
        string (RFC 2254)
        :param limit: The maximum number of accounts to return
        (0 is default and means all)
        :param offset: The starting offset (0, 25, etc)
        :param domain: The domain name to limit the search to
        :param applyCos: applyCos - Flag whether or not to apply the COS
        policy to account. Specify 0 (false) if only requesting attrs that
        aren't inherited from COS
        :param applyConfig: whether or not to apply the global config attrs to
        account. specify 0 (false) if only requesting attrs that aren't
        inherited from global config
        :param sortBy: Name of attribute to sort on. Default is the account
        name.
        :param types: Comma-separated list of types to return. Legal values
        are: accounts|distributionlists|aliases|resources|domains|coses
        (default is accounts)
        :param sortAscending: Whether to sort in ascending order. Default is
        1 (true)
        :param countOnly: Whether response should be count only. Default is
        0 (false)
        :param attrs: Comma-seperated list of attrs to return ("displayName",
        "zimbraId", "zimbraAccountStatus")
        :return: dict of list of "account" "alias" "dl" "calresource" "domain"
        "cos"
        """

        search_response = self.request('SearchDirectory', kwargs)

        result = {}
        items = {
            "account": zobjects.Account.from_dict,
            "domain": zobjects.Domain.from_dict,
            "dl": zobjects.DistributionList.from_dict,
            "cos": zobjects.COS.from_dict,
            "calresource": zobjects.CalendarResource.from_dict
            # "alias": TODO,
        }

        for obj_type, func in items.items():
            if obj_type in search_response:
                if isinstance(search_response[obj_type], list):
                    result[obj_type] = [
                        func(v) for v in search_response[obj_type]]
                else:
                    result[obj_type] = func(search_response[obj_type])
        return result


class ZimbraMailClient(ZimbraAbstractClient):
    """ Specialized Soap client to access zimbraMail webservice.

    API ref is
    http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/zimbraMail/service-summary.html
    """
    NAMESPACE = 'urn:zimbraMail'
    LOCATION = 'service/soap'
    REST_PREAUTH = MailRESTClient

    def __init__(self, server_host, server_port='443', *args, **kwargs):
        super(ZimbraMailClient, self).__init__(
            server_host, server_port,
            *args, **kwargs)

    def _return_comma_list(self, l):
        """ get a list and return a string with comma separated list values
        Examples ['to', 'ta'] will return 'to,ta'.
        """
        if isinstance(l, (text_type, int)):
            return l

        if not isinstance(l, list):
            raise TypeError(l, ' should be a list of integers, \
not {0}'.format(type(l)))

        str_ids = ','.join(str(i) for i in l)

        return str_ids

    def is_session_valid(self):
        # zimbraMail do not have by itself an Auth request, so create a
        # zimbraAccount client for that check.
        zac = ZimbraAccountClient(self._server_host, self._server_port)
        zac._session.import_session(self._session.authToken)
        return zac.is_session_valid()

    def login(self, user, password):
        # !!! We need to authenticate with the 'urn:zimbraAccount' namespace
        self._session.login(user, password, 'urn:zimbraAccount')

    # Permissions

    def get_permission(self, right):
        return self.request(
            'GetPermission',
            {'ace': {'right': {'_content': right}}}
        )

    def grant_permission(self, right, zid=None, grantee_name=None, gt='usr'):
        params = {'ace': {
            'gt': gt,
            'right': right
        }}

        if grantee_name:
            params['ace']['d'] = grantee_name
        elif zid:
            params['ace']['zid'] = zid
        else:
            raise TypeError('at least zid or grantee_name should be set')

        return self.request('GrantPermission', params)

    def revoke_permission(self, right, zid=None, grantee_name=None, gt='usr'):
        params = {'ace': {
            'gt': gt,
            'right': right
        }}

        if grantee_name:
            params['ace']['d'] = grantee_name
        elif zid:
            params['ace']['zid'] = zid
        else:
            raise TypeError('missing zid or grantee_name')

        self.request('RevokePermission', params)

    # Ranking action
    def reset_ranking(self):
        """Reset the contact ranking table for the account
        """
        self.request('RankingAction', {'action': {'op': 'reset'}})

    def delete_ranking(self, email):
        """Delete a specific address in the auto-completion of the users

        :param email: the address to remove
        """
        self.request('RankingAction', {'action': {'op': 'reset',
                                                  'email': email
                                                  }})

    # Task

    def create_task(self, subject, desc):
        """Create a task

        :param subject: the task's subject
        :param desc: the task's content in plain-text
        :returns: the task's id
        """
        task = zobjects.Task()
        task_creator = task.to_creator(subject, desc)
        resp = self.request('CreateTask', task_creator)
        task_id = resp['calItemId']
        return task_id

    def get_task(self, task_id):
        """Retrieve one task, discriminated by id.

        :param: task_id: the task id

        :returns: a zobjects.Task object ;
                  if no task is matching, returns None.
        """
        task = self.request_single('GetTask', {'id': task_id})

        if task:
            return zobjects.Task.from_dict(task)
        else:
            return None

    # Contact

    def create_contact(self, attrs, members=None, folder_id=None, tags=None):
        """Create a contact

        Does not include VCARD nor group membership yet

        XML example :
        <cn l="7> ## ContactSpec
            <a n="lastName">MARTIN</a>
            <a n="firstName">Pierre</a>
            <a n="email">pmartin@example.com</a>
        </cn>
        Which would be in zimsoap : attrs = { 'lastname': 'MARTIN',
                                        'firstname': 'Pierre',
                                        'email': 'pmartin@example.com' }
                                    folder_id = 7

        :param folder_id: a string of the ID's folder where to create
        contact. Default '7'
        :param tags:     comma-separated list of tag names
        :param attrs:   a dictionary of attributes to set ({key:value,...}). At
        least one attr is required
        :returns:       the created zobjects.Contact
        """
        cn = {}
        if folder_id:
            cn['l'] = str(folder_id)
        if tags:
            tags = self._return_comma_list(tags)
            cn['tn'] = tags
        if members:
            cn['m'] = members

        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        cn['a'] = attrs
        resp = self.request_single('CreateContact', {'cn': cn})

        return zobjects.Contact.from_dict(resp)

    def get_contacts(self, ids=None):
        """ Get all contacts for the current user

        :param ids: An coma separated list of contact's ID to look for

        :returns: a list of zobjects.Contact
        """
        params = {}
        if ids:
            ids = self._return_comma_list(ids)
            params['cn'] = {'id': ids}

        contacts = self.request_list('GetContacts', params)

        return [zobjects.Contact.from_dict(i) for i in contacts]

    def modify_contact(self, contact_id, attrs=None, members=None, tags=None):
        """
        :param contact_id: zimbra id of the targetd contact
        :param attrs  : a dictionary of attributes to set ({key:value,...})
        :param members: list of dict representing contacts and
        operation (+|-|reset)
        :param tags:    comma-separated list of tag names
        :returns:       the modified zobjects.Contact
        """
        cn = {}
        if tags:
            tags = self._return_comma_list(tags)
            cn['tn'] = tags
        if members:
            cn['m'] = members
        if attrs:
            attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
            cn['a'] = attrs

        cn['id'] = contact_id
        resp = self.request_single('ModifyContact', {'cn': cn})

        return zobjects.Contact.from_dict(resp)

    def delete_contacts(self, ids):
        """ Delete selected contacts for the current user

        :param ids: list of ids
        """

        str_ids = self._return_comma_list(ids)
        self.request('ContactAction', {'action': {'op': 'delete',
                                                  'id': str_ids}})

    def create_group(self, attrs, members, folder_id=None, tags=None):
        """Create a contact group

        XML example :
        <cn l="7> ## ContactSpec
            <a n="lastName">MARTIN</a>
            <a n="firstName">Pierre</a>
            <a n="email">pmartin@example.com</a>
        </cn>
        Which would be in zimsoap : attrs = { 'lastname': 'MARTIN',
                                        'firstname': 'Pierre',
                                        'email': 'pmartin@example.com' }
                                    folder_id = 7

        :param folder_id: a string of the ID's folder where to create
        contact. Default '7'
        :param tags:     comma-separated list of tag names
        :param members:  list of dict. Members with their type. Example
        {'type': 'I', 'value': 'manual_addresse@example.com'}.
        :param attrs:   a dictionary of attributes to set ({key:value,...}). At
        least one attr is required
        :returns:       the created zobjects.Contact
        """
        cn = {}
        cn['m'] = members

        if folder_id:
            cn['l'] = str(folder_id)
        if tags:
            cn['tn'] = tags

        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        attrs.append({'n': 'type', '_content': 'group'})
        cn['a'] = attrs
        resp = self.request_single('CreateContact', {'cn': cn})

        return zobjects.Contact.from_dict(resp)

    # Folder

    def create_folder(self, name, parent_id='1'):
        params = {'folder': {
            'name': name,
            'l': parent_id
        }}

        return self.request('CreateFolder', params)['folder']

    def create_mountpoint(self, name, path=None, owner=None, parent_id='1'):
        """
        :param name: Mountpoint path
        :param parent_id: folder id of where mountpoint will be created
        :param path:  Path to shared item
        :param owner:  Primary email address of the owner of the
        linked-to resource
        """
        params = {'link': {
            'name': name,
            'l': parent_id,
            'path': path,
            'owner': owner
        }}

        return self.request('CreateMountpoint', params)['link']

    def delete_folders(self, paths=None, folder_ids=None):
        """
        :param folder_ids: list of ids
        :param path: list of folder's paths
        """
        if folder_ids:
            f_ids = folder_ids
        elif paths:
            f_ids = []
            for path in paths:
                folder = self.get_folder(path=path)
                f_ids.append(folder['folder']['id'])

        comma_ids = self._return_comma_list(f_ids)

        params = {'action': {
            'id': comma_ids,
            'op': 'delete'
        }}

        self.request('FolderAction', params)

    def delete_mountpoints(self, paths=None, folder_ids=None):
        """
        :param folder_ids: list of ids
        :param path: list of folder's paths
        """
        self.delete_folders(paths=paths, folder_ids=folder_ids)

    def get_folder(self, f_id=None, path=None, uuid=None):
        request = {'folder': {}}
        if f_id:
            request['folder']['l'] = str(f_id)
        if uuid:
            request['folder']['uuid'] = str(uuid)
        if path:
            request['folder']['path'] = str(path)

        return self.request('GetFolder', request)

    def get_folder_grant(self, **kwargs):
        folder = self.get_folder(**kwargs)
        if 'acl' in folder['folder']:
            return folder['folder']['acl']
        else:
            return None

    def modify_folder_grant(
        self,
        folder_ids,
        perm,
        zid=None,
        grantee_name=None,
        gt='usr',
        flags=None
    ):
        """
        :param folder_ids: list of ids
        :param perm: permission to grant to the user on folder(s)
        :param zid: id of user to grant rights
        :param grantee_name: email address of user to grant rights
        :param flags: folder's flags
        """
        f_ids = self._return_comma_list(folder_ids)

        params = {'action': {
            'id': f_ids,
            'op': 'grant',
            'grant': {'perm': perm, 'gt': gt}
        }}

        if perm == 'none':
            params['action']['op'] = '!grant'
            params['action']['zid'] = zid
            # Remove key to raise Zimsoap exception if no zid provided
            if not zid:
                params['action'].pop('zid', None)

        if grantee_name:
            params['action']['grant']['d'] = grantee_name
        elif zid:
            params['action']['grant']['zid'] = zid
        else:
            raise TypeError('missing zid or grantee_name')

        self.request('FolderAction', params)

    def modify_folders(
        self, folder_ids, color=None, flags=None, parent_folder=None,
        name=None, num_days=None, rgb=None, tags=None, view=None
    ):
        """
        :param folder_ids: list of ids
        :param color: color numeric; range 0-127; defaults to 0 if not present;
        client can display only 0-7
        :param flags: flags
        :param parent_folder: id of new location folder
        :param name: new name for the folder
        :param tags: list of tag names
        :param view: list of tag view
        """
        f_ids = self._return_comma_list(folder_ids)

        params = {'action': {
            'id': f_ids,
            'op': 'update',
        }}

        if color:
            params['action']['color'] = color
        if flags:
            params['action']['f'] = flags
        if parent_folder:
            params['action']['l'] = parent_folder
        if name:
            params['action']['name'] = name
        if tags:
            tn = self._return_comma_list(tags)
            params['action']['tn'] = tn
        if view:
            params['action']['view'] = view

        self.request('FolderAction', params)

    # Conversation

    def get_conversation(self, conv_id, **kwargs):
        content = {'c': kwargs}
        content['c']['id'] = int(conv_id)

        return self.request('GetConv', content)

    def delete_conversations(self, ids):
        """ Delete selected conversations

        :params ids: list of ids
        """

        str_ids = self._return_comma_list(ids)
        self.request('ConvAction', {'action': {'op': 'delete',
                                               'id': str_ids
                                               }})

    def move_conversations(self, ids, folder):
        """ Move selected conversations to an other folder

        :params ids: list of ids
        :params folder: folder id
        """

        str_ids = self._return_comma_list(ids)
        self.request('ConvAction', {'action': {'op': 'move',
                                               'id': str_ids,
                                               'l': str(folder)}})

    # Messages

    def add_message(self, msg_content, folder, **kwargs):
        """ Inject a message

        :params string msg_content: The entire message's content.
        :params string folder: Folder pathname (starts with '/') or folder ID
        """
        content = {'m': kwargs}
        content['m']['l'] = str(folder)
        content['m']['content'] = {'_content': msg_content}

        return self.request('AddMsg', content)

    def get_message(self, msg_id, **kwargs):
        content = {'m': kwargs}
        content['m']['id'] = str(msg_id)

        return self.request('GetMsg', content)

    def move_messages(self, ids, folder_id):
        """ Move selected messages to an other folder

        :param msg_ids: list of message's ids to move
        :param folder_id: folder's id where to move messages
        """
        str_ids = self._return_comma_list(ids)
        params = {'action': {
            'id': str_ids,
            'op': 'move',
            'l': folder_id
        }}

        self.request('MsgAction', params)

    def update_messages_flag(self, ids, flag):
        """
        List of flags :
        u -> unread                 f -> flagged
        a -> has attachment         s -> sent by me
        r -> replied                w -> forwarded
        d -> draft                  x -> deleted
        n -> notification sent

        by default a message priority is "normal" otherwise:
        ! -> priority high          ? -> priority low
        """
        str_ids = self._return_comma_list(ids)
        params = {'action': {
            'id': str_ids,
            'op': 'update',
            'f': flag
        }}

        self.request('MsgAction', params)

    def delete_messages(self, ids):
        """ Delete selected messages for the current user

        :param ids: list of ids
        """
        str_ids = self._return_comma_list(ids)
        return self.request('MsgAction', {'action': {'op': 'delete',
                                                     'id': str_ids}})

    # Search
    def search(self, query, **kwargs):
        """ Search object in account

        :returns: a dic where value c contains the list of results (if there
        is any). Example : {
            'more': '0',
            'offset': '0',
            'sortBy': 'dateDesc',
            'c': [
                {
                    'id': '-261',
                    'm': {'id': '261',
                          's': '2556',
                          'l': '2'},
                    'u': '0', 'd': '1450714720000',
                    'sf': '1450714720000',
                    'e': {'t': 'f',
                          'd': 'kokopu',
                          'a': 'kokopu@zimbratest3.example.com'},
                    'n': '1',
                    'fr': {'_content': 'Hello there !'},
                    'su': {'_content': 'The subject is cool'}
                }
            ]
        """

        content = kwargs
        content['query'] = {'_content': query}

        return self.request('Search', content)

    # DataSource

    def create_data_source(self, data_source, dest_folder):
        """ Create data source from a dict
        data_source example =
        {
            'pop3': {
                'leaveOnServer': "(0|1)", 'id': 'data-source-id',
                'name': 'data-source-name',
                'isEnabled': '(0|1)', 'importOnly': '(0|1)',
                'host': 'data-source-server', 'port': 'data-source-port',
                'connectionType': '(cleartext|ssl|tls|tls_is_available)',
                'username': 'data-source-username',
                'password': 'data-source-password',
                'emailAddress': 'data-source-address',
                'useAddressForForwardReply': '(0|1)',
                'defaultSignature': 'default-signature-id',
                'forwardReplySignature': 'forward-reply-signature-id',
                'fromDisplay': 'data-source-from-display',
                'replyToAddress': 'data-source-replyto-address',
                'replyToDisplay': 'data-source-replyto-display',
                'importClass': 'data-import-class',
                'failingSince': 'data-source-failing-since'
            }
        }
        """
        folder = self.create_folder(dest_folder)
        for type_source, source_config in data_source.items():
            data_source[type_source]['l'] = folder['id']
        return self.request('CreateDataSource', data_source)

    def get_data_sources(self, types=[], source_addresses=[], source_id=None):
        all_data_sources = self.request('GetDataSources')

        data_sources = {}
        if types and source_addresses:
            for t in types:
                data_sources = {t: []}
                if t in all_data_sources and isinstance(all_data_sources[t],
                                                        list):
                    for data_source in all_data_sources[t]:
                        if data_source['emailAddress'] in source_addresses:
                            data_sources[t].append(data_source)
                elif t in all_data_sources and isinstance(all_data_sources[t],
                                                          dict):
                    if all_data_sources[t]['emailAddress'] in source_addresses:
                        data_sources[t].append(all_data_sources[t])

        elif types and not source_addresses:
            for t in types:
                data_sources = {t: []}
                if t in all_data_sources and isinstance(all_data_sources[t],
                                                        list):
                    for data_source in all_data_sources[t]:
                        data_sources[t].append(data_source)
                elif t in all_data_sources and isinstance(all_data_sources[t],
                                                          dict):
                    data_sources[t].append(all_data_sources[t])

        elif source_addresses and not types:
            for t in all_data_sources.keys():
                if isinstance(all_data_sources[t], list):
                    for data_source in all_data_sources[t]:
                        if data_source['emailAddress'] in source_addresses:
                            try:
                                data_sources[t].append(data_source)
                            except KeyError:
                                data_sources = {t: []}
                                data_sources[t].append(data_source)
                elif isinstance(all_data_sources[t], dict):
                    if all_data_sources[t]['emailAddress'] in source_addresses:
                        try:
                            data_sources[t].append(all_data_sources[t])
                        except KeyError:
                            data_sources = {t: []}
                            data_sources[t].append(all_data_sources[t])

        elif source_id:
            for t in all_data_sources.keys():
                data_sources = {t: []}
                if isinstance(all_data_sources[t], list):
                    for data_source in all_data_sources[t]:
                        if data_source['id'] == source_id:
                            data_sources[t].append(data_source)
                elif isinstance(all_data_sources[t], dict):
                    if all_data_sources[t]['id'] == source_id:
                        data_sources[t].append(all_data_sources[t])

        else:
            return all_data_sources

        return data_sources

    def modify_data_source(self, data_source):
        """ Modify data source from a dict
        data_source example =
        {
            'pop3': {
                'leaveOnServer': "(0|1)", 'id': 'data-source-id',
                'name': 'data-source-name', 'l': 'data-source-folder-id',
                'isEnabled': '(0|1)', 'importOnly': '(0|1)',
                'host': 'data-source-server', 'port': 'data-source-port',
                'connectionType': '(cleartext|ssl|tls|tls_is_available)',
                'username': 'data-source-username',
                'password': 'data-source-password',
                'emailAddress': 'data-source-address',
                'useAddressForForwardReply': '(0|1)',
                'defaultSignature': 'default-signature-id',
                'forwardReplySignature': 'forward-reply-signature-id',
                'fromDisplay': 'data-source-from-display',
                'replyToAddress': 'data-source-replyto-address',
                'replyToDisplay': 'data-source-replyto-display',
                'importClass': 'data-import-class',
                'failingSince': 'data-source-failing-since'
            }
        }
        """
        return self.request('ModifyDataSource', data_source)

    def delete_data_source(self, data_source):
        """
        Delete data source with it's name or ID.
        data_source = { 'imap': {'name': 'data-source-name'}}
        or
        data_source = { 'pop3': {'id': 'data-source-id'}}
        """
        source_type = [k for k in data_source.keys()][0]
        complete_source = self.get_data_sources(
            source_id=data_source[source_type]['id'])
        folder_id = complete_source[source_type][0]['l']
        self.delete_folders(folder_ids=[folder_id])
        return self.request('DeleteDataSource', data_source)


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
                'account': zobjects.Account(name=username).to_selector(),
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
