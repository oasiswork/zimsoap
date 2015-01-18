#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys; import os; sys.path.append(os.path.dirname(__file__)+'/../')

from urllib2 import URLError

import zimsoap.client
from zimsoap.zobjects import *

zc = zimsoap.client.ZimbraAdminClient("192.168.2.103", "7071")
try:
    zc.login("manens@manens.org", "")
except (zimsoap.client.ZimbraSoapServerError, URLError) as sf:
    print sf
    exit(5)

account = zc.delegate_auth(Account(name="demo2@manens.org"))
#a2 = zc.get_account_mailbox(name="demo2@manens.org")
account = zc.get_account("demo2@manens.org")
print(account)
#a = zc.get_account(account)
#print(a)
