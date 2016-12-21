from zimsoap import zobjects


class MethodMixin:
    def get_all_domains(self):
        """ Fetches the details of all the domains

        :returns: a list of domain objects
        :rtype:   [zobjects.admin.Domain]
        """
        return self.request_list('GetAllDomains', {}, zobjects.admin.Domain)

    def get_domain(self, domain):
        """ Fetches the information of a domain

        :param domain: the domain to use as a selector
        :type domain:  zobjects.admin.Domain

        :returns: the domain object
        :rtype:   zobjects.admin.Domain or None
        """
        selector = domain.to_selector()
        return self.request_single(
            'GetDomain', {'domain': selector}, zobjects.admin.Domain)

    def create_domain(self, name):
        """ Creates a new domain

        :param name: the domain name
        :type name:  str

        :returns: the creates domain object
        :rtype:   zobjects.admin.Domain or None
        """
        args = {'name': name}
        return self.request_single('CreateDomain', args, zobjects.admin.Domain)

    def modify_domain(self, domain, attrs):
        """ Modifies a domain

        :param domain: the domain to use as a selector
        :type domain:  zobjects.admin.Domain
        :param attrs: attributes to modify
        :type attrs:  dict

        :return: the modified domain object
        :rtype:  zobjects.admin.Domain
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        return self.request_single('ModifyDomain', {
            'id': self._get_or_fetch_id(domain, self.get_domain),
            'a': attrs
        }, zobjects.admin.Domain)

    def delete_domain(self, domain):
        """ Deletes a domain

        :param domain: the domain to use as a selector
        :type domain:  zobjects.admin.Domain

        :returns: None (the API returns nothing)
        """
        self.request('DeleteDomain', {
            'id': self._get_or_fetch_id(domain, self.get_domain)
        })

    def delete_domain_forced(self, domain):
        """ Deletes a domain, even if it has items (accounts, lists, ...)

        :param domain: the domain to use as a selector
        :type domain:  zobjects.admin.Domain

        :returns: None (the API returns nothing)
        """
        # Remove aliases and accounts
        # we take all accounts because there might be an alias
        # for an account of an other domain
        accounts = self.get_all_accounts()
        for a in accounts:
            if 'zimbraMailAlias' in a._props:
                aliases = a._props['zimbraMailAlias']
                if isinstance(aliases, list):
                    for alias in aliases:
                        if alias.split('@')[1] == domain.name:
                            self.remove_account_alias(a, alias)
                else:
                    if aliases.split('@')[1] == domain.name:
                        self.remove_account_alias(a, aliases)
            if a.name.split('@')[1] == domain.name:
                self.delete_account(a)

        # Remove resources
        resources = self.get_all_calendar_resources(domain=domain)
        for r in resources:
            self.delete_calendar_resource(r)

        # Remove distribution lists
        dls = self.get_all_distribution_lists(domain)
        for dl in dls:
            self.delete_distribution_list(dl)

        self.request('DeleteDomain', {
            'id': self._get_or_fetch_id(domain, self.get_domain)
        })
