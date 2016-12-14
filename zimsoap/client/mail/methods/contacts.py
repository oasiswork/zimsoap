from zimsoap import zobjects


class MethodMixin:
    def create_contact(self, attrs, members=None, folder_id=None, tags=None):
        """Create a contact

        Does not include VCARD nor group membership yet

        XML example :
        <cn l="7> ## ContactSpec
            <a n="lastName">MARTIN</a>
            <a n="firstName">Pierre</a>
            <a n="email">pmartin@example.com</a>
        </cn>
        Which would be in zimsoap : attrs = { 'lastname': 'MARTIN',
                                        'firstname': 'Pierre',
                                        'email': 'pmartin@example.com' }
                                    folder_id = 7

        :param folder_id: a string of the ID's folder where to create
        contact. Default '7'
        :param tags:     comma-separated list of tag names
        :param attrs:   a dictionary of attributes to set ({key:value,...}). At
        least one attr is required
        :returns:       the created zobjects.Contact
        """
        cn = {}
        if folder_id:
            cn['l'] = str(folder_id)
        if tags:
            tags = self._return_comma_list(tags)
            cn['tn'] = tags
        if members:
            cn['m'] = members

        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        cn['a'] = attrs
        resp = self.request_single('CreateContact', {'cn': cn})

        return zobjects.Contact.from_dict(resp)

    def get_contacts(self, ids=None, **kwargs):
        """ Get all contacts for the current user

        :param l: string of a folder id
        :param ids: An coma separated list of contact's ID to look for

        :returns: a list of zobjects.Contact
        """
        params = {}
        if ids:
            ids = self._return_comma_list(ids)
            params['cn'] = {'id': ids}

        for key, value in kwargs.items():
            if key in ['a', 'ma']:
                params[key] = {'n': value}
            else:
                params[key] = value

        contacts = self.request_list('GetContacts', params)

        return [zobjects.Contact.from_dict(i) for i in contacts]

    def modify_contact(self, contact_id, attrs=None, members=None, tags=None):
        """
        :param contact_id: zimbra id of the targetd contact
        :param attrs  : a dictionary of attributes to set ({key:value,...})
        :param members: list of dict representing contacts and
        operation (+|-|reset)
        :param tags:    comma-separated list of tag names
        :returns:       the modified zobjects.Contact
        """
        cn = {}
        if tags:
            tags = self._return_comma_list(tags)
            cn['tn'] = tags
        if members:
            cn['m'] = members
        if attrs:
            attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
            cn['a'] = attrs

        cn['id'] = contact_id
        resp = self.request_single('ModifyContact', {'cn': cn})

        return zobjects.Contact.from_dict(resp)

    def delete_contacts(self, ids):
        """ Delete selected contacts for the current user

        :param ids: list of ids
        """

        str_ids = self._return_comma_list(ids)
        self.request('ContactAction', {'action': {'op': 'delete',
                                                  'id': str_ids}})

    def create_group(self, attrs, members, folder_id=None, tags=None):
        """Create a contact group

        XML example :
        <cn l="7> ## ContactSpec
            <a n="lastName">MARTIN</a>
            <a n="firstName">Pierre</a>
            <a n="email">pmartin@example.com</a>
        </cn>
        Which would be in zimsoap : attrs = { 'lastname': 'MARTIN',
                                        'firstname': 'Pierre',
                                        'email': 'pmartin@example.com' }
                                    folder_id = 7

        :param folder_id: a string of the ID's folder where to create
        contact. Default '7'
        :param tags:     comma-separated list of tag names
        :param members:  list of dict. Members with their type. Example
        {'type': 'I', 'value': 'manual_addresse@example.com'}.
        :param attrs:   a dictionary of attributes to set ({key:value,...}). At
        least one attr is required
        :returns:       the created zobjects.Contact
        """
        cn = {}
        cn['m'] = members

        if folder_id:
            cn['l'] = str(folder_id)
        if tags:
            cn['tn'] = tags

        attrs = [{'n': k, '_content': v} for k, v in attrs.items()]
        attrs.append({'n': 'type', '_content': 'group'})
        cn['a'] = attrs
        resp = self.request_single('CreateContact', {'cn': cn})

        return zobjects.Contact.from_dict(resp)
