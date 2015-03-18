ZimSOAP : a programmatic python interface to zimbra
===================================================

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
 - all requests are tested with 8.0.4 and 8.0.5

[SOAP Zimbra API]:
http://files.zimbra.com/docs/soap_api/8.0.4/soap-docs-804/api-reference/index.html
[python-zimbra]:https://github.com/Zimbra-Community/python-zimbra/

Installing
----------

**Till [this PR](https://github.com/Zimbra-Community/python-zimbra/pull/16) is
  worked out and released, requires a patched version of python-zimbra**.

Install it with :

    pip install git+https://github.com/oasiswork/python-zimbra.git@utf-encoding-requests

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
all Zimbra accounts/domains/settings are disposable for automated tests
purposes.

----


### Setting your environment for tests ###

Most of tests are Integration tests are to be run either :

- against a pre-configured VM, using vagrant
- using any zimbra server you provide, after reading the above warning.


#### Using the vagrant VM ####

There is a VM ready for you with vagrant, just make sure you have vagrant installed and then :

    $ vagrant up 8.0.5
    $ vagrant provision 8.0.5

You have several zimbra versions available as VMs for testing (see vagrant
status).

*Warning*: the test VM requires 2GB RAM to function properly and may put heavy
 load on your machine.

#### Using your own zimbra server ####

Be sure to have a server:
- running zimbra 8.x,
- ports 7071 and 443 reachables
- with an unix user having password-less sudo rights

First delete all accounts/domains/calendar resources from your test server and run :

    cat tests/provision-01-test-data.zmprov | ssh user@mytestserver -- sudo su - zimbra -c | zmprov

(considering *mytestserver* is your server hostname and *user* is a unix user with admin sudo rights)

It will provision an admin account, but disabled. You have to set a password and enable the account

    ssh user@mytestserver -- sudo su - zimbra -c 'zmprov sp admin@zimbratest.example.com mypassword'
    ssh user@mytestserver -- sudo su - zimbra -c 'zmprov ma admin@zimbratest.example.com zimbraAccountStatus active'

Then create a *test_config.ini* in tests/ directory. Example content:

    [zimbra_server]
    host = mytestserver
    admin_port = 7071
    admin_login = admin@zimbratest.example.com
    admin_password = mypassword

If you damaged the data with failed tests, you can just delete everything except
the admin account and then run :

    cat tests/provision-01-test-data.zmprov | ssh user@mytestserver -- sudo su - zimbra -c | zmprov

### Testing ###

After you are all set, you can run tests
[the standard python way](https://docs.python.org/2/library/unittest.html)

    $ python -m unittest discover

… Or using [py.test](http://pytest.org/).

    $ py.test
