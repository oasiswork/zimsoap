""" Contains the server settings of unit tests.

You can change them to what suit your name, but the tests are only suposed to
be passing with the reference test VMs (see README.md) and their reference
provisionned accounts.
"""

TEST_HOST="192.168.33.10"
TEST_ADMIN_PORT="7071"

TEST_DOMAIN1="zimbratest.oasiswork.fr"
TEST_DOMAIN2="zimbratest2.oasiswork.fr"
TEST_DOMAIN13="zimbratest3.oasiswork.fr"

TEST_ADMIN_LOGIN="admin@"+TEST_DOMAIN1
TEST_ADMIN_PASSWORD="password"

TEST_LAMBDA_USER="albacore@"+TEST_DOMAIN1
TEST_LAMBDA_PASSWORD="albacore"
