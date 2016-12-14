from zimsoap import zobjects


class MethodMixin:
    def get_all_calendar_resources(self, domain=None, server=None,):
        selectors = {}
        if domain:
            selectors['domain'] = domain.to_selector()
        if server:
            selectors['server'] = server.to_selector()

        dict_calres = self.request_list('GetAllCalendarResources', selectors)

        resources = []
        for i in dict_calres:
            calres = zobjects.CalendarResource.from_dict(i)
            resources.append(calres)

        return resources

    def get_calendar_resource(self, cal_resource):
        """ Fetches an calendar resource with all its attributes.

        :param account: a CalendarResource, with either id or
                        name attribute set.
        :returns: a CalendarResource object, filled.
        """
        selector = cal_resource.to_selector()
        resp = self.request_single('GetCalendarResource',
                                   {'calresource': selector})
        return zobjects.CalendarResource.from_dict(resp)

    def create_calendar_resource(self, name, password=None, attrs={}):
        """
        :param: attrs a dict of attributes, must specify the displayName and
                     zimbraCalResType
        """
        args = {
            'name': name,
            'a': [{'n': k, '_content': v} for k, v in attrs.items()]
            }
        if password:
            args['password'] = password
        resp = self.request_single('CreateCalendarResource', args)
        return zobjects.CalendarResource.from_dict(resp)

    def delete_calendar_resource(self, calresource):
        self.request('DeleteCalendarResource', {
            'id': self._get_or_fetch_id(calresource,
                                        self.get_calendar_resource),
        })

    def modify_calendar_resource(self, calres, attrs):
        """
        :param calres: a zobjects.CalendarResource
        :param attrs:    a dictionary of attributes to set ({key:value,...})
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        self.request('ModifyCalendarResource', {
            'id': self._get_or_fetch_id(
                calres, self.get_calendar_resource),
            'a': attrs
        })

    def rename_calendar_resource(self, r_description, new_r_name):
        """
        :param r_description : a CalendarResource specifying either :
                   - id:   the ressource ID
                   - r_description: the name of the ressource
        :param new_r_name: new name of the list
        :return: a zobjects.CalendarResource
        """
        resp = self.request('RenameCalendarResource', {
            'id': self._get_or_fetch_id(r_description,
                                        self.get_calendar_resource),
            'newName': new_r_name
        })

        return zobjects.CalendarResource.from_dict(resp['calresource'])
