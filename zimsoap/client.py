#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Zimbra SOAP client pythonic abstraction

core classes for SOAP clients, there are also REST clients here, but used only
for pre-authentification.
"""


from os.path import dirname, abspath, join
import datetime
import urllib
import urllib2
import cookielib
import time

import pysimplesoap

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
            self.preauth_url = 'https://{}:{}/service/preauth?'.format(
                server_host, server_port)
        else:
            self.preauth_url = 'https://{}/service/preauth?'.format(server_host)

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


class ShouldAuthenticateFirst(Exception):
    """ Error fired when an operation requiring auth is intented before the auth
    is done.
    """
    pass


class DomainHasNoPreAuthKey(Exception):
    """ Error fired when the server has no preauth key
    pass"""
    def __init__(self, domain):
        # Call the base class constructor with the parameters it needs
        msg = '"{}" has no preauth key, make one first, see {}'.format(
            domain.name,
            'http://wiki.zimbra.com/wiki/Preauth#Preparing_a_domain_for_preauth'
            )
        Exception.__init__(self)


class ZimbraAbstractClient(pysimplesoap.client.SoapClient):
    """ Factorized abstract code for SOAP API access.

    Provides common ground for zimbraAdmin and zimbraAccount.
    """
    def __init__(self, server_host, server_port, *args, **kwargs):
        loc = 'https://%s:%s/%s' % (server_host, server_port, self.LOCATION)
        self._server_host = server_host
        self._server_port = server_port
        super(ZimbraAbstractClient, self).__init__(
            location = loc,
            action = loc,
            namespace = self.NAMESPACE,
            *args, **kwargs)

        self._session = ZimbraAPISession(self)

    def login(self, user, password):
        self._session.login(user, password)
        self['context'] = self._session.get_context_header()

    def login_with_authToken(self, authToken, lifetime=None):
        self._session.import_session(authToken)
        self['context'] = self._session.get_context_header()
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
        @param  name        verbose name of the signature
        @param  content     content of the signature, in html or plain-text
        @param  contenttype can be "text/html" (default) or "text/plain"
        @return a zobjects.Signature object
        """
        s = zobjects.Signature(name=name)
        s.set_content(content, contenttype)
        resp = self.CreateSignatureRequest(self,
                                           utils.wrap_el(s.to_xml_creator()))
        xml_sig = utils.extractSingleResponse(resp)
        return zobjects.Signature.from_xml(xml_sig)

    def get_signatures(self):
        """ Get all signatures for the current user

        @returns a list of zobjects.Signature
        """
        resp = self.GetSignaturesRequest()
        return [zobjects.Signature.from_xml(i) for i in utils.extractResponses(resp)]

    def get_signature(self, signature):
        """Retrieve one signature, discriminated by name or id.

        @param a zobjects.Signature describing the signature
               like "Signature(name='my-sig')"

        @returns a zobjects.Signature object, filled with the signature.
        """

        resp = self.GetSignaturesRequest(
            self, utils.wrap_el(signature.to_xml_selector()))
        return zobjects.Signature.from_xml(utils.extractSingleResponse(resp))


    def delete_signature(self, signature):
        """ Delete a signature by name or id

        @param signature a Signature object with name or id defined
        """
        self.DeleteSignatureRequest(
            self, utils.wrap_el(signature.to_xml_selector()))

    def modify_signature(self, signature):
        """ Modify an existing signature

        Can modify the content, contenttype and name. An unset attribute will not
        delete the attribute but leave it untouched.
        @param signature a zobject.Signature object, with modified
                         content/contentype/name, the id should be present and
                          valid, the name does not allows to identify the
                         signature for that operation.
        """

        # if no content is specified, just use a selector (id/name)
        xml = signature.to_xml_creator(for_modify=True)

        self.ModifySignatureRequest(self, utils.wrap_el(xml))

    def get_preferences(self):
        """ Gets all the preferences of the current user

        @returns a dict presenting the preferences by name, values are
                 typed to str/bool/int/float regarding their content.
        """
        pref_list = utils.extractResponses(self.GetPrefsRequest())

        out = {}
        for i in pref_list:
            out[i['name']] = utils.auto_type(str(i))

        return out

    def get_preference(self, pref_name):
        """ Gets a single named preference

        @returns the value, typed to str/bool/int/float regarding its content.
        """
        xml = pysimplesoap.client.SimpleXMLElement(
            '<pref name="{}" />'.format(pref_name))
        resp = self.GetPrefsRequest(self, utils.wrap_el(xml))
        return utils.auto_type(str(utils.extractSingleResponse(resp)))

    def get_identities(self):
        """ Get all the identities of the user, as a list

        @returns list of zobjects.Identity
        """
        resps = utils.extractResponses(self.GetIdentitiesRequest())
        return [zobjects.Identity.from_xml(i) for i in resps]

    def modify_identity(self, identity):
        """ Modify some attributes of an identity or its name.

        @param identity a zobjects.Identity with `id` set (mandatory). Also set
               items you want to modify/set and/or the `name` attribute to
               rename the identity.
        """
        xml = identity.to_xml_creator()
        self.ModifyIdentityRequest(self, utils.wrap_el(xml))


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

    def get_all_domains(self):
        xml_doms = utils.extractResponses(self.GetAllDomainsRequest())
        return [zobjects.Domain.from_xml(d) for d in xml_doms]

    def get_all_accounts(self, domain=None, server=None,
                         include_system_accounts=False,
                         include_admin_accounts=True):
        selectors = []
        if domain:
            selectors.append(domain.to_xml_selector())
        if server:
            selectors.append(server.to_xml_selector())

        resp = self.GetAllAccountsRequest(self, utils.wrap_el(selectors))
        xml_accounts = utils.extractResponses(resp)

        accounts = []
        for i in xml_accounts:
            account = zobjects.Account.from_xml(i)

            if not (
                not include_system_accounts and account.is_system()
                or
                not include_admin_accounts and account.is_admin()
                ):
                accounts.append(account)

        return accounts

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

    def count_account(self, domain):
        """ Count the number of accounts for a given domain, sorted by cos

        @returns a list of pairs <ClassOfService object>,count
        """
        selector = domain.to_xml_selector()
        resp = self.CountAccountRequest(self, utils.wrap_el(selector))
        cos_list = utils.extractResponses(resp)

        ret = []

        for i in cos_list:
            ret.append( ( zobjects.ClassOfService.from_xml(i), int(i) ) )

        return list(ret)


    def get_all_mailboxes(self):
        resp = self.GetAllMailboxesRequest()
        xml_mailboxes = utils.extractResponses(resp)
        return [zobjects.Mailbox.from_xml(i) for i in xml_mailboxes]

    def get_account_mailbox(self, account_id):
        """ Returns a Mailbox corresponding to an account. Usefull to get the
        size (attribute 's'), and the mailbox ID, returns nothing appart from
        that.
        """
        selector = zobjects.Mailbox(id=account_id).to_xml_selector()
        resp = self.GetMailboxRequest(self, utils.wrap_el(selector))

        xml_mbox = utils.extractSingleResponse(resp)
        return zobjects.Mailbox.from_xml(xml_mbox)

    def get_domain(self, domain):
        selector = domain.to_xml_selector()
        resp = self.GetDomainRequest(self, utils.wrap_el(selector))
        return zobjects.Domain.from_xml(utils.extractSingleResponse(resp))

    def get_distribution_list(self, dl_description):
        """
        @param   dl_description : a DistributionList specifying either :
                   - id:   the account_id
                   - name: the name of the list
        @returns the DistributionList
        """
        selector = dl_description.to_xml_selector()

        resp = self.GetDistributionListRequest(self, utils.wrap_el(selector))
        dl = zobjects.DistributionList.from_xml(
            utils.extractSingleResponse(resp))
        return dl

    def create_distribution_list(self, name, dynamic=0):
        resp = self.CreateDistributionListRequest(attributes={
                'name'   : name,
                'dynamic': str(dynamic)
                })

        return zobjects.DistributionList.from_xml(
            utils.extractSingleResponse(resp))

    def delete_distribution_list(self, dl):
        try:
            dl_id = dl.id

        except AttributeError:
            # No id is known, so we have to fetch the dl first
            try:
                dl_id = self.get_distribution_list(dl).id
            except AttributeError:
                raise ValueError('Unqualified DistributionList')

        self.DeleteDistributionListRequest(attributes={'id': dl_id})

    def get_account(self, account):
        """ Fetches an account with all its attributes.

        @param account, an account object, with either id or name attribute set.
        @return a zobjects.Account object, filled.
        """
        req_body = utils.wrap_el(account.to_xml_selector())
        resp = self.GetAccountRequest(self, req_body)
        return zobjects.Account.from_xml(utils.extractSingleResponse(resp))

    def mk_auth_token(self, account, admin=False, duration=0):
        """ Builds an authentification token, using preauth mechanism.

        See http://wiki.zimbra.com/wiki/Preauth

        @param duration, in seconds defaults to 0, which means "use account
               default"

        @param account : an account object to be used as a selector
        @returns       the auth string
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
        xml = account.to_xml_selector()
        resp = self.DelegateAuthRequest(self, utils.wrap_el(xml))
        authToken, lifetime  = [str(i) for i in utils.extractResponses(resp)]
        zc = ZimbraAccountClient(self._server_host)
        zc.login_with_authToken(authToken, lifetime)
        return zc

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

    def login(self, username, password):
        """ Performs the login against zimbra
        (sends AuthRequest, receives AuthResponse).
        """
        req_nodes = [
            zobjects.Account(name=username).to_xml_selector(),
            pysimplesoap.client.SimpleXMLElement(
                '<password>{}</password>'.format(password)
                )
            ]

        response = self.client.AuthRequest(self.client, utils.wrap_el(req_nodes))

        # strip responses over the 2nd (useless informations such as skin...)
        self.authToken, lifetime = utils.extractResponses(response)[:2]
        lifetime = int(lifetime)
        self.authToken = str(self.authToken)
        self.set_end_date(lifetime)

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

    def import_session(self, auth_token):
        if not type(auth_token) == str:
            raise TypeError('auth_token should be a string, not {}'.format(
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
            self.client.AuthRequest(authToken=self.authToken)
            return True
        except pysimplesoap.client.SoapFault:
            return False
