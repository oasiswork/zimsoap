from zimsoap import zobjects


class MethodMixin:
    def get_all_accounts(self, domain=None, server=None,
                         include_system_accounts=False,
                         include_admin_accounts=True,
                         include_virtual_accounts=True):
        """ Get all Zimbra accounts

        :param domain:                   limit the search to accounts of a
                                         specific domain
        :type domain:                    a zobjects.admin.Domain object
        :param server:                   limit the search to accounts of a
                                         specific mailstore
        :type domain:                    a zobjects.admin.Server object
        :param include_system_accounts:  do not ignore system accounts
        :type include_system_accounts:   bool
        :param include_admin_accounts:   do not ignore admin accounts
        :type include_admin_accounts:    bool
        :param include_virtual_accounts: do not ignore virtual (external)
                                         accounts
        :type include_virtual_accounts:  bool

        :returns: a list of account objects
        :rtype:   zobjects.admin.Account
        """
        selectors = {}
        if domain:
            selectors['domain'] = domain.to_selector()
        if server:
            selectors['server'] = server.to_selector()

        dict_accounts = self.request_list('GetAllAccounts', selectors)

        accounts = []
        for i in dict_accounts:
            account = zobjects.admin.Account.from_dict(i)

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

        :param account_id: the Zimbra ID of the account we want the mailbox for
        :type account_id:  int

        :returns: the account's mailbox object
        :rtype:   zobjects.admin.Mailbox
        """
        selector = zobjects.admin.Mailbox(id=account_id).to_selector()
        resp = self.request_single('GetMailbox', {'mbox': selector})

        return zobjects.admin.Mailbox.from_dict(resp)

    def get_account_cos(self, account):
        """ Fetch the cos for a given account

        Quite different from the original request which returns COS + various
        URL + zimbraMailHost... But all other informations are accessible
        through get_account.

        :param account: the Zimbra account we want the COS for
        :type account:  zobjects.admin.Account

        :returns: a COS object
        :rtype:   zobjects.admin.COS
        """
        resp = self.request(
            'GetAccountInfo', {'account': account.to_selector()})
        return zobjects.COS.from_dict(resp['cos'])

    def get_account(self, account):
        """ Fetches an account with all its attributes.

        :param account: an account object, with either id or name attribute set
        :type account:  zobjects.admin.Account

        :returns: an account object, filled
        :rtype:   zobjects.admin.Account
        """
        selector = account.to_selector()
        resp = self.request_single('GetAccount', {'account': selector})
        return zobjects.admin.Account.from_dict(resp)

    def rename_account(self, account, new_name):
        """ Rename an account.

        :param account:  an account object with the id attribute set
        :type account:   zobjects.admin.Account
        :param new_name: the new name (email address) for the account
        :type new_name:  str

        :returns: the renamed account object
        :rtype:   zobjects.admin.Account
        """
        resp = self.request_single('RenameAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'newName': new_name
        })
        return zobjects.admin.Account.from_dict(resp)

    def modify_account(self, account, attrs):
        """ Modify the attributes of an account

        :param account: a account object with the id attribute set
        :type account:  zobjects.admin.Account
        :param attrs:   a dictionary of attributes to set ({key:value,...})
        :type attrs:    dict

        :returns: the modified account object
        :rtype:   zobjects.admin.Account
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        resp = self.request_single('ModifyAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
            'a': attrs
        })
        return zobjects.admin.Account.from_dict(resp)

    def set_password(self, account, password):
        """ Set the password for an account

        :param account:  an account object, with either id or name
                         attributes set
        :type account:   zobjects.admin.Account
        :param password: the new password
        :type password:  str

        :returns: the request response message
        :rtype:   str
        """
        resp = self.request('SetPassword', {
            'id': account.id,
            'newPassword': password
        })
        return resp['message']

    def create_account(self, email, password=None, attrs={}):
        """ Create a new account

        :param email:    full email with domain eg: login@domain.com
        :type email:     str
        :param password: password for the account
        :type password:  str
        :param attrs:    a dictionary of attributes to set ({key:value,...})

        :returns: the created account object
        :rtype:   zobjects.admin.Account
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]

        params = {'name': email, 'a': attrs}

        if password:
            params['password'] = password

        resp = self.request_single('CreateAccount', params)

        return zobjects.admin.Account.from_dict(resp)

    def delete_account(self, account):
        """
        :param account: an account object to be used as a selector
        """
        self.request('DeleteAccount', {
            'id': self._get_or_fetch_id(account, self.get_account),
        })

    def add_account_alias(self, account, alias):
        """
        :param account:   an account object to be used as a selector
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
