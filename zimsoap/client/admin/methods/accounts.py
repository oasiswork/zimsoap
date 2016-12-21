from zimsoap import zobjects


class MethodMixin:
    def get_all_accounts(self, domain=None, server=None,
                         include_system_accounts=False,
                         include_admin_accounts=True,
                         include_virtual_accounts=True):
        """ Get all Zimbra accounts

        :param domain: limit the search to accounts of a specific domain
        :type domain:  zobjects.admin.Domain
        :param server: limit the search to accounts a specific mailstore
        :type domain:  zobjects.admin.Server
        :param include_system_accounts: do not ignore system accounts
        :type include_system_accounts:  bool
        :param include_admin_accounts: do not ignore admin accounts
        :type include_admin_accounts:  bool
        :param include_virtual_accounts: do not ignore virtual (external)
                                         accounts
        :type include_virtual_accounts:  bool

        :returns: a list of account objects
        :rtype:   [zobjects.admin.Account]
        """
        selectors = {}
        if domain:
            selectors['domain'] = domain.to_selector()
        if server:
            selectors['server'] = server.to_selector()

        accounts = self.request_list(
            'GetAllAccounts', selectors, zobjects.admin.Account)

        return [a for a in accounts if not (
            not include_system_accounts and a.is_system() or
            not include_admin_accounts and a.is_admin() or
            not include_virtual_accounts and a.is_virtual()
        )]

    def get_account(self, account):
        """ Fetches an account with all its attributes.

        :param account: an account object to be used as a selector
        :type account:  zobjects.admin.Account

        :returns: an account object, filled
        :rtype:   zobjects.admin.Account or None
        """
        selector = account.to_selector()
        return self.request_single(
            'GetAccount', {'account': selector}, zobjects.admin.Account)

    def create_account(self, email, password=None, attrs={}):
        """ Create a new account

        :param email: full email with domain eg: login@domain.com
        :type email:  str
        :param password: password for the account
        :type password:  str
        :param attrs: a dictionary of attributes to set ({key:value,...})
        :type attrs:  dict

        :returns: the created account object
        :rtype:   zobjects.admin.Account or None
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]

        params = {'name': email, 'a': attrs}

        if password:
            params['password'] = password

        return self.request_single(
            'CreateAccount', params, zobjects.admin.Account)

    def rename_account(self, account, new_name):
        """ Rename an account.

        :param account: an account object with the id attribute set
        :type account:  zobjects.admin.Account
        :param new_name: the new name (email address) for the account
        :type new_name:  str

        :returns: the renamed account object
        :rtype:   zobjects.admin.Account or None
        """
        return self.request_single('RenameAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'newName': new_name
        }, zobjects.admin.Account)

    def modify_account(self, account, attrs):
        """ Modify the attributes of an account

        :param account: a account object with the id attribute set
        :type account:  zobjects.admin.Account
        :param attrs: a dictionary of attributes to set ({key:value,...})
        :type attrs:  dict

        :returns: the modified account object
        :rtype:   zobjects.admin.Account or None
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        return self.request_single('ModifyAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'a': attrs
        }, zobjects.admin.Account)

    def delete_account(self, account):
        """ Delete an account

        :param account: an account object to be used as a selector
        :type account:  zobjects.admin.Account

        :returns: None (the API returns nothing)
        """
        self.request('DeleteAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
        })

    def set_password(self, account, password):
        """ Set the password for an account

        :param account: an account object to be used as a selector
        :type account:  zobjects.admin.Account
        :param password: the new password
        :type password:  str

        :returns: None
        """
        self.request('SetPassword', {
            'id': account.id,
            'newPassword': password
        })

    def add_account_alias(self, account, alias):
        """ Add an alias to an account

        :param account: an account object to be used as a selector
        :type account:  zobjects.admin.Account
        :param alias: alias email address
        :type alias:  str

        :returns: None (the API returns nothing)
        """
        self.request('AddAccountAlias', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'alias': alias,
        })

    def remove_account_alias(self, account, alias):
        """
        :param account: an account object to be used as a selector
        :type account:  zobjects.admin.Account
        :param alias: alias email address
        :type alias:  str

        :returns: None (the API returns nothing)
        """
        self.request('RemoveAccountAlias', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'alias': alias,
        })

    def get_quota_usage(self, domain, all_servers=False,
                        limit=0, offset=0, sort_by=None,
                        sort_ascending=False, refresh=False):
        """ Fetches accounts quota usage

        :param domain: the domain name to limit the search to
        :type domain:  str
        :param all_servers: whether to fetch quota usage for all domain
                            accounts from across all mailbox servers
        :type all_servers:  bool
        :param limit: the number of accounts to return (default: all)
        :type limit:  int
        :param offset: the starting offset
        :type offset:  int
        :param sort_by: one of 'percentUsed', 'totalUsed', 'quotaLimit'
        :type sort_by:  str
        :param sort_ascending: whether to sort in ascending quota order
        :type sort_ascending:  bool
        :param refresh: whether to always recalculate the data even when
                        cached values are available
        :type refresh:  bool

        :returns: A AccountQuota object
        :rtype:   zobjects.admin.AccountQuota
        """
        params = {
            'domain': domain,
            'allServers': all_servers,
            'limit': limit,
            'offset': 0,
            'sortAscending': sort_ascending,
            'refresh': refresh
        }

        valid_sort_by = ('percentUsed', 'totalUsed', 'quotaLimit')

        if sort_by is not None:
            if sort_by not in valid_sort_by:
                raise Exception('sortBy must be one of: {}'.format(
                    '.'.join(valid_sort_by)))
            params['sortBy'] = sort_by

        return self.request_list(
            'GetQuotaUsage', params, zobjects.admin.AccountQuota)
