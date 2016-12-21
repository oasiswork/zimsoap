import re


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


class NotEnoughInformation(Exception):
    """Raised when we try to get information on an object but have too litle
    data to infer it."""
    pass


class InvalidZObjectError(Exception):
    """Raised when the ZObject we are working with does not have a valid
    structure."""
    pass
