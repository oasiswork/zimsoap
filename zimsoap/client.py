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
import time

import utils
import zobjects

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

    def get_logged_in_by(self, login, parent_zc, duration=0):
        """Use another client to get logged in via preauth mechanism by an
        already logged in admin.
        """
        preauth_str = parent_zc.mk_auth_token(zobjects.Account(name=login))

        # workaround the fact delegatedauth is only available in
        # zimbraAccoun. WARNING, this is not thread safe.
        old_namespace = self.namespace
        self.namespace = 'urn:zimbraAccount'
        # self.location.replace('/admin/soap', '/preauth')
        self._session.login(login, preauth_str, True, duration)
        # self.location.replace('/preauth','/admin/soap')
        #self.namespace = old_namespace


    def get_all_domains(self):
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

    def mk_auth_token(self, account, admin=False, duration=0):
        """ Builds an authentification token, using preauth mechanism.

        http://wiki.zimbra.com/wiki/Preauth

        @param duration, in seconds defaults to 0, which means "use account
               default"

        @param account : an account object to be used as a selector
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


class ZimbraAPISession:
    """Handle the login, the session expiration and the generation of the
       authentification header.
    """
    def __init__(self, client):
        self.client = client
        self.authToken = None

    def login(self, username, password, preauth=False, preauth_expires=0):
        """ Performs the login agains zimbra
        (sends AuthRequest, receives AuthResponse).

        @param preauth if True, provide a preauth token instead of a password
        @param preauth_expires in seconds
        """
        if preauth:
            n = '<account by="name">{}</account>'.format(username)
            p = '<preauth timestamp="{}" expires="{}">{}</preauth>'\
                .format(int(time.time())*1000, preauth_expires*1000, password)

            wrapped = utils.wrap_el((
                pysimplesoap.client.SimpleXMLElement(n),
                pysimplesoap.client.SimpleXMLElement(p),
                ))
            wrapped

            response = self.client.AuthRequest(self.client, wrapped)
        else:
            response = self.client.AuthRequest(name=username, password=password)

        # strip responses over the 2nd (useless informations such as skin...)
        self.authToken, lifetime = utils.extractResponses(response)[:2]
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
        if not self.authToken or not self.is_session_valid() or\
                not self.is_session_valid():
            return False
        return self.end_date >= datetime.datetime.now()

    def is_session_valid(self):
        try:
            self.client.AuthRequest(authToken=self.authToken)
            return True
        except pysimplesoap.client.SoapFault:
            return False


