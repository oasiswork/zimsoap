from zimsoap import utils


class MethodMixin:
    def get_preferences(self):
        """ Gets all the preferences of the current user

        :returns: a dict presenting the preferences by name, values are
                 typed to str/bool/int/float regarding their content.
        """
        pref_list = self.request('GetPrefs')['pref']

        out = {}
        for pref in pref_list:
            out[pref['name']] = utils.auto_type(pref['_content'])

        return out

    def get_preference(self, pref_name):
        """ Gets a single named preference

        :returns: the value, typed to str/bool/int/float regarding its content.
        """
        resp = self.request_single('GetPrefs', {'pref': {'name': pref_name}})
        return utils.auto_type(resp['_content'])
