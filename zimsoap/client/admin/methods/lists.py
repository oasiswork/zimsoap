from zimsoap import zobjects


class MethodMixin:
    def get_all_distribution_lists(self, domain=None):
        """ Fetches all distribution lists info, possibly limited to a domain

        :param domain: limit the search to lists of a specific domain
        :type domain:  zobjects.admin.Domain

        :returns: a list of Distribution List objects
        :rtype:   [zobjects.admin.DistributionList]
        """
        params = {}
        if domain is not None:
            params['domain'] = domain.to_selector()

        return self.request_list(
            'GetAllDistributionLists', params, zobjects.admin.DistributionList)

    def get_distribution_list(self, dl):
        """ Fetches the info for a distribution list

        :param dl: the DistributionList object to use as a selector
        :type dl:  zobjects.admin.DistributionList

        :returns: the DistributionList object populated with all info
        :rtype:   zobjects.admin.DistributionList
        """
        return self.request_single(
            'GetDistributionList', {'dl': dl.to_selector()},
            zobjects.admin.DistributionList)

    def create_distribution_list(self, name, memberURL=None, attrs={}):
        """ Creates a new distribution list

        :param name: the email address for the new distribution list
        :type name:  str
        :param memberURL: a LDAP query string to create a dynamic
                          distribution list
                          (eg: "ldap:///??sub?(objectClass=zimbraAccount")
        :type memberURL:  str
        :param attrs: attributes to set for the new list
        :type attrs:  dict

        :returns: the created distribution list object
        :rtype:   zobjects.admin.DistributionList
        """
        params = {
            'name': name,
            'a': [{'n': k, '_content': v} for k, v in attrs.items()]
        }

        if memberURL is not None:
            params['dynamic'] = True
            if 'zimbraIsACLGroup' not in attrs:
                params['a'].append(
                    {'n': 'zimbraIsACLGroup', '_content': False})

        return self.request_single(
            'CreateDistributionList', params, zobjects.admin.DistributionList)

    def modify_distribution_list(self, dl, attrs):
        """ Modifies an existing distribution list

        :param dl: the DistributionList object to use as a selector
        :type dl:  zobjects.admin.DistributionList
        :param attrs: a dictionary of attributes to set ({key:value,...})
        :type attrs:  dict

        :returns: the modified distribution list object
        :rtype:   zobjects.admin.DistributionList
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]

        return self.request_single('ModifyDistributionList', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list),
            'a': attrs
        }, zobjects.admin.DistributionList)

    def rename_distribution_list(self, dl, new_name):
        """ Changes the email address of a distribution list

        :param dl: the DistributionList object to use as a selector
        :type dl:  zobjects.admin.DistributionList
        :param new_name: new email address for the list
        :type new_name:  str

        :returns: the renamed distribution list object
        :rtype:   zobjects.admin.DistributionList
        """
        return self.request_single('RenameDistributionList', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list),
            'newName': new_name
        }, zobjects.admin.DistributionList)

    def delete_distribution_list(self, dl):
        """ Deletes a distribution list

        :param dl: the DistributionList object to use as a selector
        :type dl:  zobjects.admin.DistributionList

        :returns: None (the API returns nothing)
        """
        self.request('DeleteDistributionList', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list)
        })

    def add_distribution_list_alias(self, dl, alias):
        """ Adds an alias address to a distribution list

        :param dl: the DistributionList object to use as a selector
        :type dl:  zobjects.admin.DistributionList
        :param alias: the alias email address to add
        :type alias:  str

        :returns: None (the API returns nothing)
        """
        self.request('AddDistributionListAlias', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list),
            'alias': alias,
        })

    def remove_distribution_list_alias(self, dl, alias):
        """ Removes an alias address from a distribution list

        :param dl: the DistributionList object to use as a selector
        :type dl:  zobjects.admin.DistributionList
        :param alias: the alias email address to remove
        :type alias:  str

        :returns: None (the API returns nothing)
        """
        self.request('RemoveDistributionListAlias', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list),
            'alias': alias,
        })

    def add_distribution_list_member(self, dl, members):
        """ Adds members to a distribution list

        :param dl: the DistributionList object to use as a selector
        :type dl:  zobjects.admin.DistributionList
        :param members: list of email addresses to add
        :type members:  [str]

        :returns: None (the API returns nothing)
        """
        members = [{'_content': v} for v in members]

        self.request('AddDistributionListMember', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list),
            'dlm': members
        })

    def remove_distribution_list_member(self, dl, members):
        """ Removes members from a distribution list

        :param dl: the DistributionList object to use as a selector
        :type dl:  zobjects.admin.DistributionList
        :param members: list of email addresses to remove
        :type members:  [str]

        :returns: None (the API returns nothing)
        """
        members = [{'_content': v} for v in members]

        self.request('RemoveDistributionListMember', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list),
            'dlm': members
        })
