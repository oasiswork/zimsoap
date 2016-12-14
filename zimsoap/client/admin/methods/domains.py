from zimsoap import zobjects


class MethodMixin:
    def get_all_domains(self):
        resp = self.request_list('GetAllDomains')
        return [zobjects.Domain.from_dict(d) for d in resp]

    def count_account(self, domain):
        """ Count the number of accounts for a given domain, sorted by cos

        :returns: a list of pairs <ClassOfService object>,count
        """
        selector = domain.to_selector()
        cos_list = self.request_list('CountAccount', {'domain': selector})
        ret = []

        for i in cos_list:
            count = int(i['_content'])
            ret.append((zobjects.ClassOfService.from_dict(i),  count))

        return list(ret)

    def get_quota_usage(self, domain, all_servers=False,
                        limit=None, offset=None, sort_by=None,
                        sort_ascending=None, refresh=None):
        content = {}
        content['domain'] = domain
        content['allServers'] = all_servers

        if limit:
            content['limit'] = limit
        if sort_by:
            content['sortBy'] = sort_by
        if sort_ascending:
            content['sortAscending'] = sort_ascending
        if refresh:
            content['refresh'] = refresh

        resp = self.request_list('GetQuotaUsage', content)

        return resp

    def create_domain(self, name):
        """
        :param name: A string, NOT a zObject
        :return: a zobjects.Domain
        """
        args = {'name': name}
        resp = self.request_single('CreateDomain', args)

        return zobjects.Domain.from_dict(resp)

    def delete_domain(self, domain):
        self.request('DeleteDomain', {
            'id': self._get_or_fetch_id(domain, self.get_domain)
        })

    def delete_domain_forced(self, domain):
        # Remove aliases and accounts
        # we take all accounts because there might be an alias
        # for an account of an other domain
        accounts = self.get_all_accounts()
        for a in accounts:
            if 'zimbraMailAlias' in a._a_tags:
                aliases = a._a_tags['zimbraMailAlias']
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

    def get_domain(self, domain):
        selector = domain.to_selector()
        resp = self.request_single('GetDomain', {'domain': selector})
        return zobjects.Domain.from_dict(resp)

    def modify_domain(self, domain, attrs):
        """
        :type domain: a zobjects.Domain
        :param attrs: attributes to modify
        :type attrs dict
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        self.request('ModifyDomain', {
            'id': self._get_or_fetch_id(domain, self.get_domain),
            'a': attrs
        })
