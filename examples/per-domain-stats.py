#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# WARNING: NOT UP-TO-DATE.
#
# Remaining here as an example only, not as a tool.
# Check oazim-tools at https://dev.oasiswork.fr/projects/oazim-tools for
# up-to-date code.
#

import argparse
import getpass

import sys; import os; sys.path.append(os.path.dirname(__file__)+'/../')

from urllib2 import URLError

import zimsoap.client
from zimsoap.zobjects import *


def parse_args():
    parser = argparse.ArgumentParser(description=\
      'Counts Zimbra accounts, globally or for a subset of domains, sorted by cos.')
    parser.add_argument("-u", "--username", required=True,
                        help="zimbra admin username (user@domain.tld)")
    parser.add_argument("-s", "--server",required=True,
                        help="zimbra server host or proxy")

    parser.add_argument("-p", "--port", default=7071,
                        help="server or proxy port (default : 7071)")
    parser.add_argument("--domain", '-d', action="append", nargs="*",
                        help="restrict the stats to this domain")
    args = parser.parse_args()

    if args.domain:
        # Flattens a list of lists.
        args.domains_list = [i for sublist in args.domain for i in sublist]

    return args


if __name__ == '__main__':
    print 'WARNING: this is an example script, do not use in production'
    args = parse_args()
    password = getpass.getpass('Password for %s: ' % args.username)

    zc = zimsoap.client.ZimbraAdminClient(args.server, args.port)
    try:
        zc.login(args.username, password)
    except (zimsoap.client.ZimbraSoapServerError, URLError) as sf:
        print sf
        exit(5)

    if args.domain:
        domains_to_inspect = [Domain(name=i) for i in args.domains_list]
    else:
        domains_to_inspect = zc.get_all_domains()

    total_accounts = 0

    print "\nPrint accounts count, per-COS:"
    for domain in domains_to_inspect:
        print
        print "Domain %s" % domain.name
        for cos , count in zc.count_account(domain):
            print '{:.<20}{}'.format(cos.name, count)
            total_accounts += count

print '\nTOTAL ACCOUNTS ({} domains): {}'.format(
    len(domains_to_inspect), total_accounts)
