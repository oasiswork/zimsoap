from zimsoap import zobjects


class MethodMixin:
    def get_all_config(self):
        """ Fetches the values of all global config attributes

        :returns: a dict-like Config object
        :rtype:   zobjects.admin.Config or None
        """
        return self.request_single('GetAllConfig', {}, zobjects.admin.Config)

    def get_config(self, attr):
        """ Fetches the value of a single global config attribute

        :param attr: the name of the config attribute
        :type attr:  str

        :returns: the value of the config attribute
                  (a list if nulti-valued attribute)
        :rtype:   any
        """
        config = self.request_single(
            'GetConfig', {'a': {'n': attr}}, zobjects.admin.Config)
        if attr in config.properties():
            return config[attr]
        else:
            raise KeyError('{} not found'.format(attr))

    def modify_config(self, attr, value):
        """ Sets the value a global config attribute

        :param attr:  the name of the config attribute
        :type attr:   str
        :param value: the desired value for the attribute
        :type value:  str

        :returns: the value of the attribute fetched from Zimbra
                  after modification
        :rtype:   [str]
        """
        self.request('ModifyConfig', {
            'a': {
                'n': attr,
                '_content': value
            }})
        if attr[0] == '-' or attr[0] == '+':
            attr = attr[1::]
        return self.get_config(attr)
