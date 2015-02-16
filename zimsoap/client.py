#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Zimbra SOAP client pythonic abstraction

core classes for SOAP clients, there are also REST clients here, but used only
for pre-authentification.
"""

import datetime
import urllib
import urllib2
import cookielib
import time
import re

import pythonzimbra

import pythonzimbra.tools.auth
from pythonzimbra.communication import Communication

import utils
import zobjects


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
            self.preauth_url = 'https://{0}/service/preauth?'.format(server_host)

        self.set_preauth_key(preauth_key)

    def set_preauth_key(self, preauth_key):
        self.preauth_key = preauth_key

    def get_preauth_token(self, account_name, expires=0):
        if not self.preauth_key:
            raise self.NoPreauthKeyProvided

        ts = int(time.time())*1000

        preauth_str = utils.build_preauth_str(self.preauth_key, account_name,
                                              ts, expires, admin=self.isadmin)

        args = urllib.urlencode({
                'account'   : account_name,
                'by'        : 'name',
                'timestamp' : ts,
                'expires'   : expires*1000,
                'admin'     : "1" if self.isadmin else "0",
                'preauth'   : preauth_str
                })

        cj = cookielib.CookieJar()
        browser = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj))

        try:
            browser.open(self.preauth_url+args)
            for cookie in cj:
                if cookie.name == self.TOKEN_COOKIE:
                    return cookie.value

        except urllib2.HTTPError, e:
            raise self.RESTBackendError(e)


class AdminRESTClient(RESTClient):
    TOKEN_COOKIE = 'ZM_ADMIN_AUTH_TOKEN'
    def __init__(self, server_host, server_port=7071, preauth_key=None):
        self.isadmin = True
        RESTClient.__init__(self,server_host, server_port, preauth_key)


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
    pass"""
    def __init__(self, domain):
        # Call the base class constructor with the parameters it needs
        msg = '"{0}" has no preauth key, make one first, see {1}'.format(
            domain.name,
            'http://wiki.zimbra.com/wiki/Preauth#Preparing_a_domain_for_preauth'
            )
        Exception.__init__(self)

class ZimbraSoapServerError(ZimSOAPException):
    r_soap_text = re.compile(r'<soap:Text>(.*)</soap:Text>')
    def __init__(self, http_e, request, response):
        self.http_e = http_e
        self.request = request
        self.response = response
        self.http_msg = self.r_soap_text.search(self.http_e.read()).groups()[0]

    def __str__(self):
        return '{0}: {1}'.format(
            self.http_e, self.http_msg)

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
        req = auth_request = pythonzimbra.request_xml.RequestXml()
        resp = pythonzimbra.response_xml.ResponseXml()

        if self._session.is_logged_in():
            req.set_auth_token(self._session.authToken)

        req.add_request(req_name, content, namespace)
        try:
            self.com.send_request(req, resp)
        except urllib2.HTTPError, e:
            if e.code == 500:
                raise ZimbraSoapServerError(e, req, resp)
            else:
                raise

        try:
            return resp.get_response()[resp_name]
        except KeyError:
            raise ZimbraSoapUnexpectedResponse(
                req, resp, 'Cannot find {} in response "{}"'.format(
                    resp_name, resp.get_response()))

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
        #self['context'] = self._session.get_context_header()

    def login_with_authToken(self, authToken, lifetime=None):
        self._session.import_session(authToken)
        #self['context'] = self._session.get_context_header()
        if lifetime:
            self._session.set_end_date(int(lifetime))


    def get_logged_in_by(self, login, parent_zc, duration=0):
        """Use another client to get logged in via preauth mechanism by an
        already logged in admin.
        """
        domain_name = zobjects.Account(name=login).get_domain()
        preauth_key = parent_zc.get_domain(domain_name)['zimbraPreAuthKey']

        rc = self.REST_PREAUTH(
            self._server_host, parent_zc._server_port, preauth_key=preauth_key)

        authToken = rc.get_preauth_token(login)

        self.login_with_authToken(authToken)

    def get_host(self):
        return self._server_host


class ZimbraAccountClient(ZimbraAbstractClient):
    """ Specialized Soap client to access zimbraAccount webservice.

    API ref is
    http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/zimbraAccount/service-summary.html
    """
    NAMESPACE='urn:zimbraAccount'
    LOCATION='service/soap'
    REST_PREAUTH=AccountRESTClient

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
                    its_this_one = (sig.name == signature.name)
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

        Can modify the content, contenttype and name. An unset attribute will not
        delete the attribute but leave it untouched.
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

        if resp.has_key('identity'):
            identities = resp['identity']
            if type(identities) != list:
                identities = [identities]

            return [zobjects.Identity.from_dict(i) for i in identities]
        else:
            return []

    def modify_identity(self, identity):
        """ Modify some attributes of an identity or its name.

        :param: identity a zobjects.Identity with `id` set (mandatory). Also set
               items you want to modify/set and/or the `name` attribute to
               rename the identity.
        """
        self.request('ModifyIdentity', {'identity': identity.to_creator()})


class ZimbraAdminClient(ZimbraAbstractClient):
    """ Specialized Soap client to access zimbraAdmin webservice, handling auth.

    API ref is
    http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/zimbraAdmin/service-summary.html
    """
    NAMESPACE='urn:zimbraAdmin'
    LOCATION='service/admin/soap'
    REST_PREAUTH=AdminRESTClient

    def __init__(self, server_host, server_port='7071',
                 *args, **kwargs):
        super(ZimbraAdminClient, self).__init__(
            server_host, server_port,
            *args, **kwargs)

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
                not include_system_accounts and account.is_system()
                or
                not include_admin_accounts and account.is_admin()
                or
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

        :param: account, a CalendarResource, with either id or name attribute set.
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
            'name'    : name,
            'a'       : [{'n': k, '_content': v} for k,v in attrs.items()]
            }
        if password:
            args['password'] = password
        resp = self.request_single('CreateCalendarResource', args)
        return zobjects.CalendarResource.from_dict(resp)

    def delete_calendar_resource(self, calresource):
        self.request('DeleteCalendarResource', {
            'id': self._get_or_fetch_id(calresource, self.get_calendar_resource),
        })

    def modify_calendar_resource(self, calres, attrs):
        """
        :param account: a zobjects.CalendarResource
        :param attrs:    a dictionary of attributes to set ({key:value,...})
        """
        attrs = [{'n': k, '_content': v} for k,v in attrs.items()]
        self.request('ModifyCalendarResource', {
                'id': self._get_or_fetch_id(calres, self.get_calendar_resource),
                'a' : attrs
        })

    # Mailbox stats

    def get_mailbox_stats(self):
        """ Get global stats about mailboxes

        Parses <stats numMboxes="6" totalSize="141077"/>

        :returns: dict with stats
        """
        resp = self.request_single('GetMailboxStats')
        ret = {}
        for k,v in resp.items():
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
        attrs = [{'n': k, '_content': v} for k,v in attrs.items()]
        self.request('ModifyDomain', {
                'id': self._get_or_fetch_id(domain, self.get_domain),
                'a' : attrs
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
        args = {'name'   : name, 'dynamic': str(dynamic)}
        resp = self.request_single('CreateDistributionList', args)

        return zobjects.DistributionList.from_dict(resp)

    def delete_distribution_list(self, dl):
        self.request('DeleteDistributionList', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list)
        })

    def get_account(self, account):
        """ Fetches an account with all its attributes.

        :param account: an account object, with either id or name attribute set.
        :returns: a zobjects.Account object, filled.
        """
        selector = account.to_selector()
        resp = self.request_single('GetAccount', {'account': selector})
        return zobjects.Account.from_dict(resp)


    def modify_account(self, account, attrs):
        """
        :param account: a zobjects.Account
        :param attrs  : a dictionary of attributes to set ({key:value,...})
        """
        attrs = [{'n': k, '_content': v} for k,v in attrs.items()]
        self.request('ModifyAccount', {
                'id': self._get_or_fetch_id(account, self.get_account),
                'a' : attrs
        })

    def create_account(self, email, password, attrs={}):
        """
        :param email:    Full email with domain eg: login@domain.com
        :param password: Password for local auth
        :param attrs:    a dictionary of attributes to set ({key:value,...})
        :returns:        the created zobjects.Account
        """
        attrs = [{'n': k, '_content': v} for k,v in attrs.items()]
        resp = self.request_single('CreateAccount', {
                'name': email,
                'password' : password,
                'a': attrs,
        })

        return zobjects.Account.from_dict(resp)

    def delete_account(self, account):
        """
        :param acccount: an account object to be used as a selector
        """
        self.request('DeleteAccount', {
                'id': self._get_or_fetch_id(account, self.get_account),
        })

    def add_account_alias(self, account, alias):
        """
        :param acccount:  an account object to be used as a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('AddAccountAlias', {
                'id': self._get_or_fetch_id(account, self.get_account),
                'alias': alias,
        })

    def remove_account_alias(self, account, alias):
        """
        :param acccount:  an account object to be used as a selector
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
        selector = account.to_selector()
        resp = self.request('DelegateAuth', {'account': selector})

        lifetime = resp['lifetime']['_content']
        authToken = resp['authToken']['_content']

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

        authToken = resp['authToken']['_content']
        lifetime = int(resp['lifetime']['_content'])

        return authToken, lifetime


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

    def login(self, user, password):
        # !!! We need to authenticate with the 'urn:zimbraAccount' namespace
        self._session.login(user, password, 'urn:zimbraAccount')

    def _extract_folders(self, folders, prefix=""):
        result = []
        if not "name" in folders:
            # log.debug("Unknown Object: %s" % unicode(folders))
            pass
        else:
            if folders["name"] == "USER_ROOT":
                foldername = "/"
                folders["name"] = foldername
            else:
                foldername = "%s/%s" % (prefix, folders["name"])
                prefix = foldername
                folders["name"] = foldername
            if "folder" in folders:
                if "name" in folders["folder"]:
                    folders["folder"]["name"] = "%s/%s" % (foldername, folders["folder"]["name"])
                    result.append(zobjects.Folder.from_dict(folders["folder"]))
                else:
                    for folder in folders["folder"]:
                        result.extend(self._extract_folders(folder, prefix))
                del folders["folder"]
            if "link" in folders:
                # No folder or link under a link
                if "name" in folders["link"]:
                    if foldername == "/":
                        folders["link"]["name"] = "/%s" % (folders["link"]["name"])
                    else:
                        folders["link"]["name"] = "%s/%s" % (foldername, folders["link"]["name"])
                    result.append(zobjects.Link.from_dict(folders["link"]))
                else:
                    for link in folders["link"]:
                        link["name"] = "%s/%s" % (prefix, link["name"])
                        if hasattr(link, "folder"):
                            del link.folder
                        result.append(zobjects.Link.from_dict(link))
            if "search" in folders:
                # No folder or link under a link
                if "name" in folders["search"]:
                    if foldername == "/":
                        folders["search"]["name"] = "/%s" % (folders["search"]["name"])
                    else:
                        folders["search"]["name"] = "%s/%s" % (foldername, folders["search"]["name"])
                    result.append(zobjects.Search.from_dict(folders["search"]))
                else:
                    for search in folders["search"]:
                        search["name"] = "%s/%s" % (prefix, search["name"])
                        result.append(zobjects.Search.from_dict(search))
            result.append(zobjects.Folder.from_dict(folders))
        return result

    def get_folders(self, visible=1, needGranteeName=1, view=None, depth=-1, tr=True):
        """ Fetches all folders of an account.

        :param account: an account object, with either id or name attribute set.
        :returns: a zobjects.Folders object, filled.
        """
        folders = self.request_single('GetFolder',
                                      {"visible": visible, "needGranteeName": needGranteeName, "view": view,
                                       "depth": depth, "tr": tr})

        return self._extract_folders(folders)

    def get_folder(self, folder, visible=1, needGranteeName=1, view=None, depth=-1, tr=True):
        """ Fetches one folder of an account.

        :param folder: an Folder object, with path attribute set.
        :returns: a zobjects.Folders object, filled.
        """
        resp = self.request_single('GetFolder', {"folder": {"path": folder.path}, "visible": visible,
                                                 "needGranteeName": needGranteeName, "view": view, "depth": depth,
                                                 "tr": tr})

        return zobjects.Folder.from_dict(resp)

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

        :param: namespace if specified, the namespace used for authetication (if
                         the client namespace is not suitable for
                         authentication).
        """

        if namespace == None:
            namespace = self.client.NAMESPACE

        data = self.client.request(
            'Auth',
            {
                'account': zobjects.Account(name=username).to_selector(),
                'password': {'_content': password}
             }
            , namespace)
        self.authToken = data['authToken']['_content']
        lifetime = int(data['lifetime']['_content'])

        self.authToken = str(self.authToken)
        self.set_end_date(lifetime)

    def import_session(self, auth_token):
        if not isinstance(auth_token, (str, unicode)):
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
