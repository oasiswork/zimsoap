import time
import warnings

# import zimsoap.client.admin.methods as methods
# from zimsoap.client.admin.methods import *
from zimsoap import utils
from zimsoap import zobjects
from zimsoap.rest import AdminRESTClient
from zimsoap.exceptions import DomainHasNoPreAuthKey
from zimsoap.client import ZimbraAbstractClient
from zimsoap.client.account import ZimbraAccountClient

from . import methods


class ZimbraAdminClient(
        ZimbraAbstractClient,
        methods.accounts.MethodMixin,
        methods.config.MethodMixin,
        methods.domains.MethodMixin,
        methods.lists.MethodMixin,
        methods.mailboxes.MethodMixin,
        methods.resources.MethodMixin):

    """ Specialized Soap client to access zimbraAdmin webservice, handling auth.

    API ref is
    http://files.zimbra.com/docs/soap_api/<zimbra version>/api-reference/zimbraAdmin/service-summary.html  # noqa

    See mixins in methods directory for API requests implementations.
    """
    NAMESPACE = 'urn:zimbraAdmin'
    LOCATION = 'service/admin/soap'
    REST_PREAUTH = AdminRESTClient

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
