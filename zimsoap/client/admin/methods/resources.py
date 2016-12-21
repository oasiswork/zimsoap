from zimsoap import zobjects


class MethodMixin:
    def get_all_calendar_resources(self, domain=None, server=None,):
        """ Fetches all calendar resources info, possibly limited to a domain
        or server

        :param domain: limit the search to resources of a specific domain
        :type domain:  zobjects.admin.Domain
        :param server: limit the search to resources a specific mailstore
        :type domain:  zobjects.admin.Server

        :returns: a list of CalendarResource objects
        :rtype:   [zobjects.admin.CalendarResource]
        """
        params = {}
        if domain:
            params['domain'] = domain.to_selector()
        if server:
            params['server'] = server.to_selector()

        return self.request_list(
            'GetAllCalendarResources', params, zobjects.admin.CalendarResource)

    def get_calendar_resource(self, res):
        """ Fetches an calendar resource with all its attributes.

        :param res: a calendar resource to use as a selector
        :type res:  zobjects.admin.CalendarResource

        :returns: a CalendarResource object populated with all info
        :rtype:   zobjects.admin.CalendarResource
        """
        return self.request_single(
            'GetCalendarResource', {'calresource': res.to_selector()},
            zobjects.admin.CalendarResource)

    def create_calendar_resource(
            self, name, res_type, password=None, attrs={}):
        """ Creates a new calendar resource

        :param name: the email address for the new calendar resource
        :type name:  str
        :param res_type: the calendar resource type
                         (must be one of "Equipment" or "Location")
        :type res_type:  str
        :param name: an optional password
        :type name:  str
        :param attrs: attributes to set for the new calendar resource
                      (must specify zimbraCalResType)
        :type attrs:  dict

        :returns: the created calendar resource object
        :rtype:   zobjects.admin.CalendarResource
        """
        allowed_types = (
            zobjects.admin.CalendarResource.EQUIPMENT_TYPE,
            zobjects.admin.CalendarResource.LOCATION_TYPE,
        )
        if res_type not in allowed_types:
            raise ValueError('res_type must be one of "{}"'.format(
                '" or "'.join(allowed_types)))
        attrs.pop('zimbraCalResType', None)

        if 'displayName' not in attrs:
            attrs['displayName'] = name

        params = {
            'name': name,
            'a': [{'n': k, '_content': v} for k, v in attrs.items()]
        }
        params['a'].append({'n': 'zimbraCalResType', '_content': res_type})

        if password:
            params['password'] = password

        return self.request_single(
            'CreateCalendarResource', params, zobjects.admin.CalendarResource)

    def modify_calendar_resource(self, res, attrs):
        """ Modifies an existing calendar resource

        :param res: a calendar resource to use as a selector
        :type res:  zobjects.admin.CalendarResource
        :param attrs: a dictionary of attributes to set ({key:value,...})
        :type attrs:  dict

        :returns: the modified calendar resource object
        :rtype:   zobjects.admin.CalendarResource
        """
        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]

        return self.request_single('ModifyCalendarResource', {
            'id': self._get_or_fetch_id(res, self.get_calendar_resource),
            'a': attrs
        }, zobjects.admin.CalendarResource)

    def rename_calendar_resource(self, res, new_name):
        """ Changes the email address of a calendar resource

        :param res: a calendar resource to use as a selector
        :type res:  zobjects.admin.CalendarResource
        :param new_name: new email address for the list
        :type new_name:  str

        :returns: the renamed calendar resource object
        :rtype:   zobjects.admin.CalendarResource
        """
        return self.request_single('RenameCalendarResource', {
            'id': self._get_or_fetch_id(res, self.get_calendar_resource),
            'newName': new_name
        }, zobjects.admin.CalendarResource)

    def delete_calendar_resource(self, res):
        """ Deletes a calendar resource

        :param res: a calendar resource to use as a selector
        :type res:  zobjects.admin.CalendarResource

        :returns: None (the API returns nothing)
        """
        self.request('DeleteCalendarResource', {
            'id': self._get_or_fetch_id(res, self.get_calendar_resource)})
