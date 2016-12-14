# import zimsoap.client.account.methods as methods
# from zimsoap.client.account.methods import *
from zimsoap.rest import AccountRESTClient
from zimsoap.client import ZimbraAbstractClient

from zimsoap.client.account import methods


class ZimbraAccountClient(
        ZimbraAbstractClient,
        methods.identities.MethodMixin,
        methods.preferences.MethodMixin,
        methods.shares.MethodMixin,
        methods.signatures.MethodMixin,
        methods.wblists.MethodMixin):

    """ Specialized Soap client to access zimbraAccount webservice.

    API ref is
    http://files.zimbra.com/docs/soap_api/<zimbra version>/api-reference/zimbraAccount/service-summary.html  # noqa

    See mixins in methods directory for API requests implementations.
    """
    NAMESPACE = 'urn:zimbraAccount'
    LOCATION = 'service/soap'
    REST_PREAUTH = AccountRESTClient

    def __init__(self, server_host, server_port='443', *args, **kwargs):
        super(ZimbraAccountClient, self).__init__(
            server_host, server_port,
            *args, **kwargs)
