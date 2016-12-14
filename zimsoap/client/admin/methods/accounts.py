from zimsoap import zobjects


class MethodMixin:
    def get_all_accounts(self, domain=None, server=None,
                         include_system_accounts=False,
                         include_admin_accounts=True,
                         include_virtual_accounts=True):
        selectors = {}
        if domain:
            selectors['domain'] = domain.to_selector()
        if server:
            selectors['server'] = server.to_selector()

        dict_accounts = self.request_list('GetAllAccounts', selectors)

        accounts = []
        for i in dict_accounts:
            account = zobjects.Account.from_dict(i)

            if not (
                not include_system_accounts and account.is_system() or
                not include_admin_accounts and account.is_admin() or
                not include_virtual_accounts and account.is_virtual()
            ):
                accounts.append(account)

        return accounts

    def get_account_mailbox(self, account_id):
        """ Returns a Mailbox corresponding to an account. Usefull to get the
        size (attribute 's'), and the mailbox ID, returns nothing appart from
        that.
        """
        selector = zobjects.Mailbox(id=account_id).to_selector()
        resp = self.request_single('GetMailbox', {'mbox': selector})

        return zobjects.Mailbox.from_dict(resp)

    def get_account_cos(self, account):
        """ Fetch the cos for a given account

        Quite different from the original request which returns COS + various
        URL + COS + zimbraMailHost... But all other informations are accessible
        through get_account.

        :type account: zobjects.Account
        :rtype: zobjects.COS
        """
        resp = self.request(
            'GetAccountInfo', {'account': account.to_selector()})
        return zobjects.COS.from_dict(resp['cos'])

    def get_account(self, account):
        """ Fetches an account with all its attributes.

        :param account: an account object, with either id or name attribute set
        :returns: a zobjects.Account object, filled.
        """
        selector = account.to_selector()
        resp = self.request_single('GetAccount', {'account': selector})
        return zobjects.Account.from_dict(resp)

    def rename_account(self, account, new_name):
        """ Rename an account.

        :param account: a zobjects.Account
        :param new_name: a string of new account name
        """
        self.request('RenameAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'newName': new_name
        })

    def modify_account(self, account, attrs):
        """
        :param account: a zobjects.Account
        :param attrs  : a dictionary of attributes to set ({key:value,...})
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        self.request('ModifyAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'a': attrs
        })

    def set_password(self, account, password):
        """
        :param account: a zobjects.Account
        :param password: new password to set
        """
        self.request('SetPassword', {
            'id': account.id,
            'newPassword': password
        })

    def create_account(self, email, password=None, attrs={}):
        """
        :param email:    Full email with domain eg: login@domain.com
        :param password: Password for local auth
        :param attrs:    a dictionary of attributes to set ({key:value,...})
        :returns:        the created zobjects.Account
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]

        params = {'name': email, 'a': attrs}

        if password:
            params['password'] = password

        resp = self.request_single('CreateAccount', params)

        return zobjects.Account.from_dict(resp)

    def delete_account(self, account):
        """
        :param account: an account object to be used as a selector
        """
        self.request('DeleteAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
        })

    def add_account_alias(self, account, alias):
        """
        :param account:  an account object to be used as a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('AddAccountAlias', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'alias': alias,
        })

    def remove_account_alias(self, account, alias):
        """
        :param account:  an account object to be used as a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('RemoveAccountAlias', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'alias': alias,
        })
