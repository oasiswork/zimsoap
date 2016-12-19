from zimsoap import zobjects


class MethodMixin:
    def add_distribution_list_alias(self, distribution_list, alias):
        """
        :param distribution_list:  a distribution list object to be used as
         a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('AddDistributionListAlias', {
            'id': self._get_or_fetch_id(
                distribution_list, self.get_distribution_list
                ),
            'alias': alias,
        })

    def remove_distribution_list_alias(self, distribution_list, alias):
        """
        :param distribution_list:  an distribution list object to be used as
        a selector
        :param alias:     email alias address
        :returns:         None (the API itself returns nothing)
        """
        self.request('RemoveDistributionListAlias', {
            'id': self._get_or_fetch_id(
                distribution_list, self.get_distribution_list
            ),
            'alias': alias,
        })

    def get_all_distribution_lists(self, domain=None):
        if domain:
            selectors = {'domain': domain.to_selector()}
        else:
            selectors = {}

        got = self.request_list('GetAllDistributionLists', selectors)
        return [zobjects.admin.DistributionList.from_dict(i) for i in got]

    def get_distribution_list(self, dl_description):
        """
        :param:   dl_description : a DistributionList specifying either :
                   - id:   the account_id
                   - name: the name of the list
        :returns: the DistributionList
        """
        selector = dl_description.to_selector()

        resp = self.request_single('GetDistributionList', {'dl': selector})
        dl = zobjects.admin.DistributionList.from_dict(resp)
        return dl

    def create_distribution_list(self, name, dynamic=0):
        """

        :param name: A string, NOT a zObject
        :param dynamic:
        :return: a zobjects.DistributionList
        """
        args = {'name': name, 'dynamic': str(dynamic)}
        resp = self.request_single('CreateDistributionList', args)

        return zobjects.admin.DistributionList.from_dict(resp)

    def modify_distribution_list(self, dl_description, attrs):
        """
        :param dl_description : a DistributionList specifying either :
                   - id:   the dl_list_id
                   - dl_description: the name of the list
        :param attrs  : a dictionary of attributes to set ({key:value,...})
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        self.request('ModifyDistributionList', {
            'id': self._get_or_fetch_id(dl_description,
                                        self.get_distribution_list),
            'a': attrs
        })

    def rename_distribution_list(self, dl_description, new_dl_name):
        """
        :param dl_description : a DistributionList specifying either :
                   - id:   the dl_list_id
                   - dl_description: the name of the list
        :param new_dl_name: new name of the list
        :return: a zobjects.DistributionList
        """
        resp = self.request('RenameDistributionList', {
            'id': self._get_or_fetch_id(dl_description,
                                        self.get_distribution_list),
            'newName': new_dl_name
        })

        return zobjects.admin.DistributionList.from_dict(resp['dl'])

    def delete_distribution_list(self, dl):
        self.request('DeleteDistributionList', {
            'id': self._get_or_fetch_id(dl, self.get_distribution_list)
        })

    def add_distribution_list_member(self, distribution_list, members):
        """ Adds members to the distribution list

        :type distribution_list: zobjects.DistributionList
        :param members:          list of email addresses you want to add
        :type members:           list of str
        """
        members = [{'_content': v} for v in members]
        resp = self.request_single('AddDistributionListMember', {
            'id': self._get_or_fetch_id(distribution_list,
                                        self.get_distribution_list),
            'dlm': members
        })
        return resp

    def remove_distribution_list_member(self, distribution_list, members):
        """ Removes members from the distribution list

        :type distribution_list: zobjects.DistributionList
        :param members:          list of email addresses you want to remove
        :type members:           list of str
        """
        members = [{'_content': v} for v in members]
        resp = self.request_single('RemoveDistributionListMember', {
            'id': self._get_or_fetch_id(distribution_list,
                                        self.get_distribution_list),
            'dlm': members
        })
        return resp
