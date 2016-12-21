ZimSOAP : a programmatic python interface to zimbra
===================================================

[![Build Status](https://travis-ci.org/oasiswork/zimsoap.svg?branch=master)](https://travis-ci.org/oasiswork/zimsoap)

ZimSOAP allows to access the [SOAP Zimbra API] through a programmatic,
data-type-aware  interface high-level. It also handle  authentification,
sessions, pre-authentication and delegated authentication.

Not all methods are covered, but you're welcome to wrap the ones you need and
pull-request !

If you are looking at a lower-level lib, you better look to [python-zimbra]

Allows accessing zimbraAdmin and zimbraAccount SOAP APIs

 - handle authentification
 - handle pre-authentification admin->admin and admin->Account
 - presents the request results as nice Python objects
 - all requests are tested with Zimbra 8.6.0

[SOAP Zimbra API]:https://wiki.zimbra.com/wiki/SOAP_API_Reference_Material_Beginning_with_ZCS_8
[python-zimbra]:https://github.com/Zimbra-Community/python-zimbra/

Installing
----------

Simple:

    pip install zimsoap

Or if you fetch it from git:

    ./setup.py install

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

Most of tests are integration tests, they require a live zimbra server to be
running.

The tests will assume some base data (provisioning scsripts included),
create/update some, and cleanup after themselves. They may leave garbage data in
case they crash.

----

**DO NOT USE A PRODUCTION SERVER TO RUN TESTS.**

Use a dedicated test server, unable to send emails over network and consider
that all Zimbra accounts/domains/settings are disposable for automated tests
purposes.

----

You will need a server:
- running zimbra 8.x,
- with ports 7071 and 443 reachable
- with a system user having password-less sudo rights

In the following commands, we consider that *mytestserver* is your server hostname and *user* is a unix user with admin sudo rights.

#### Prepare the test server ####

First, delete all domains/accounts/resources/lists/... from your test server.

If you're cleaning up a server previously used for testing ZimSOAP, you can run:

    ssh user@mytestserver -- sudo su - zimbra -c zmprov < tests/cleanup-test-data.zmprov

Then provision the test data :

    ssh user@mytestserver -- sudo su - zimbra -c zmprov < tests/provision-test-data.zmprov

It will provision an admin account `admin@zimbratest.example.com` with the password `password`, as well as other required elements.

#### Configure the tests ####

Create a *test_config.ini* in tests/ directory. Example content:

    [zimbra_server]
    host = mytestserver
    server_name = zmhostname
    admin_port = 7071
    admin_login = admin@zimbratest.example.com
    admin_password = password
    https_port = 443

*note: server_name is the internal server name from your zimbra server list (generally matches the hostname)*

If you damaged the data with failed tests, you will need to run the preparation steps above again.

#### Run the tests ####

After you are all set, you can run tests
[the standard python way](https://docs.python.org/2/library/unittest.html)

    $ python -m unittest discover

… Or using [py.test](http://pytest.org/).

    $ py.test

Contributing
------------

To contribute your fixes or improvements, please fork this repository and create pull requests:
- for each fix or new API method / methodset support
- with full unittest / integration test coverage for your PR

Also please make sure your code passes the *flake8* linter:

    $ pip install -r test-requirements.txt
    $ make lint

License
-------

The ZimSOAP library is Open Source and is distributed under the BSD License (three clause).

Please see the LICENSE file included with this software.
