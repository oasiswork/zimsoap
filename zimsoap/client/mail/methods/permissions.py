class MethodMixin:
    def get_permissions(self, rights=[]):
        """
        :param rights: list of rights. Possible values : 'sendAs',
        'sendOnBehalfOf'
        :return: dict with key ace with a list of rights
        """
        aces = []
        if rights:
            for right in rights:
                ace = self.request(
                    'GetPermission',
                    {'ace': {
                        'right': {'_content': right}}})

                if 'ace' in ace.keys() and isinstance(ace, list):
                    aces.extend(ace['ace'])
                elif 'ace' in ace.keys() and isinstance(ace, dict):
                    aces.append(ace['ace'])
            return {'ace': aces}

        else:
            ace = self.request('GetPermission', {})
            if 'ace' in ace.keys() and isinstance(ace['ace'], list):
                return ace
            elif 'ace' in ace.keys() and isinstance(ace['ace'], dict):
                return ace
            else:
                return {'ace': []}

    def grant_permission(self, right, zid=None, grantee_name=None, gt='usr'):
        params = {'ace': {
            'gt': gt,
            'right': right
        }}

        if grantee_name:
            params['ace']['d'] = grantee_name
        elif zid:
            params['ace']['zid'] = zid
        else:
            raise TypeError('at least zid or grantee_name should be set')

        return self.request('GrantPermission', params)

    def revoke_permission(self, right, zid=None, grantee_name=None, gt='usr'):
        params = {'ace': {
            'gt': gt,
            'right': right
        }}

        if grantee_name:
            params['ace']['d'] = grantee_name
        elif zid:
            params['ace']['zid'] = zid
        else:
            raise TypeError('missing zid or grantee_name')

        self.request('RevokePermission', params)
