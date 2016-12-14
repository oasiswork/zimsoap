from zimsoap.exceptions import ZimbraSoapServerError


class MethodMixin:
    def get_share_info(self, grantee_type=None, grantee_id=None,
                       grantee_name=None, owner=None, owner_type='name'):
        """
        :returns: list of dict representing shares informations
        """
        params = {}
        if grantee_type:
            if 'grantee' not in params.keys():
                params['grantee'] = {}
            params['grantee'].update({'type': grantee_type})
        if grantee_id:
            if 'grantee' not in params.keys():
                params['grantee'] = {}
            params['grantee'].update({'id': grantee_id})
        if grantee_name:
            if 'grantee' not in params.keys():
                params['grantee'] = {}
            params['grantee'].update({'name': grantee_name})
        if owner:
            params['owner'] = {'by': owner_type, '_content': owner}

        try:
            resp = self.request('GetShareInfo', params)
        # if user never logged in, no mailbox was created
        except ZimbraSoapServerError as e:
            if 'mailbox not found for account' in str(e):
                return []
            else:
                raise e
        if resp and isinstance(resp['share'], list):
            return resp['share']
        elif resp and isinstance(resp['share'], dict):
            return [resp['share']]
        else:
            return []
