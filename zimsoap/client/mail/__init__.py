from six import text_type

# import zimsoap.client.mail.methods as methods
from zimsoap.rest import MailRESTClient
from zimsoap.client import ZimbraAbstractClient
from zimsoap.client.account import ZimbraAccountClient

from . import methods


class ZimbraMailClient(
        ZimbraAbstractClient,
        methods.contacts.MethodMixin,
        methods.conversations.MethodMixin,
        methods.datasources.MethodMixin,
        methods.filters.MethodMixin,
        methods.folders.MethodMixin,
        methods.messages.MethodMixin,
        methods.permissions.MethodMixin,
        methods.ranking.MethodMixin,
        methods.tasks.MethodMixin):
    """ Specialized Soap client to access zimbraMail webservice.

    API ref is
    http://files.zimbra.com/docs/soap_api/<zimbra version>/api-reference/zimbraMail/service-summary.html  # noqa
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
        # zimbraMail does not have an Auth request, so create a
        # zimbraAccount client to check.
        zac = ZimbraAccountClient(self._server_host, self._server_port)
        zac._session.import_session(self._session.authToken)
        return zac.is_session_valid()

    def login(self, user, password):
        # !!! We need to authenticate with the 'urn:zimbraAccount' namespace
        self._session.login(user, password, 'urn:zimbraAccount')

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
