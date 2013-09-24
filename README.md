ZimSOAP : a programmatic python interface to zimbra
===================================================

ZimSOAP allows to access the [SOAP Zimbra API] through a programmatic interface,
taking care of authentification.

[SOAP Zimbra API]: http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/index.html

API
---

API is accessible through the ZimbraAdminClient() method. Example :

    zc = ZimbraAdminClient('myserver.example.tld')
    zc.login('username@domain.tld', 'mypassword')

    print("Domains on that zimbra instance :")
    for domain in zc.get_all_domains():
        # Each domain is a zobject.Domain instance
        print('  - %s' % domain.name)

You can also access raw SOAP methods:

    zc = ZimbraAdminClient()
    zc.login('username@domain.tld', 'mypassword')
    xml_response = self.zc.GetAllDomainsRequest()


If you want up-to-date code example, look at unit tests...


Testing
-------

Code is covered by unit tests, you can run them (only Python needed):

    $ python test.py


Requirements
------------

pysimplesoap >= 0.11 (developpment version right now)
