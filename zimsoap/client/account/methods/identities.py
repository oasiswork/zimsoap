from zimsoap import zobjects


class MethodMixin:
    def create_identity(self, name, attrs=[]):
        """ Create an Identity

        :param: name identity name
        :param: attrs list of dict of attributes (zimsoap format)
        :returns: a zobjects.Identity object
        """
        params = {
            'name': name,
            'a': attrs
        }
        resp = self.request('CreateIdentity', {'identity': params})
        return zobjects.account.Identity.from_dict(resp['identity'])

    def get_identities(self, identity=None, attrs=None):
        """ Get identities matching name and attrs
        of the user, as a list

        :param: zobjects.Identity or identity name (string)
        :param: attrs dict of attributes to return only identities matching
        :returns: list of zobjects.Identity
        """
        resp = self.request('GetIdentities')

        if 'identity' in resp:
            identities = resp['identity']
            if type(identities) != list:
                identities = [identities]

            if identity or attrs:
                wanted_identities = []

                for u_identity in [
                        zobjects.account.Identity.from_dict(i) for i in identities]:
                    if identity:
                        if isinstance(identity, zobjects.account.Identity):
                            if u_identity.name == identity.name:
                                return [u_identity]
                        else:
                            if u_identity.name == identity:
                                return [u_identity]

                    elif attrs:
                        for attr, value in attrs.items():
                            if (attr in u_identity._props and
                                    u_identity._props[attr] == value):
                                wanted_identities.append(u_identity)
                return wanted_identities
            else:
                return [zobjects.account.Identity.from_dict(i) for i in identities]
        else:
            return []

    def modify_identity(self, identity, **kwargs):
        """ Modify some attributes of an identity or its name.

        :param: identity a zobjects.Identity with `id` set (mandatory). Also
               set items you want to modify/set and/or the `name` attribute to
               rename the identity.
               Can also take the name in string and then attributes to modify
        :returns: zobjects.Identity object
        """

        if isinstance(identity, zobjects.account.Identity):
            self.request('ModifyIdentity', {'identity': identity._full_data})
            return self.get_identities(identity=identity.name)[0]
        else:
            attrs = []
            for attr, value in kwargs.items():
                attrs.append({
                    'name': attr,
                    '_content': value
                })
            self.request('ModifyIdentity', {
                'identity': {
                    'name': identity,
                    'a': attrs
                }
            })
            return self.get_identities(identity=identity)[0]

    def delete_identity(self, identity):
        """ Delete an identity from its name or id

        :param: a zobjects.Identity object with name or id defined or a string
        of the identity's name
        """
        if isinstance(identity, zobjects.account.Identity):
            self.request(
                'DeleteIdentity', {'identity': identity.to_selector()})
        else:
            self.request('DeleteIdentity', {'identity': {'name': identity}})
