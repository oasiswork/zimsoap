class MethodMixin:
    def get_folder(self, f_id=None, path=None, uuid=None):
        request = {'folder': {}}
        if f_id:
            request['folder']['l'] = str(f_id)
        if uuid:
            request['folder']['uuid'] = str(uuid)
        if path:
            request['folder']['path'] = str(path)

        return self.request('GetFolder', request)

    def create_folder(self, name, parent_id='1'):
        params = {'folder': {
            'name': name,
            'l': parent_id
        }}

        return self.request('CreateFolder', params)['folder']

    def modify_folders(
        self, folder_ids, color=None, flags=None, parent_folder=None,
        name=None, num_days=None, rgb=None, tags=None, view=None
    ):
        """
        :param folder_ids: list of ids
        :param color: color numeric; range 0-127; defaults to 0 if not present;
        client can display only 0-7
        :param flags: flags
        :param parent_folder: id of new location folder
        :param name: new name for the folder
        :param tags: list of tag names
        :param view: list of tag view
        """
        f_ids = self._return_comma_list(folder_ids)

        params = {'action': {
            'id': f_ids,
            'op': 'update',
        }}

        if color:
            params['action']['color'] = color
        if flags:
            params['action']['f'] = flags
        if parent_folder:
            params['action']['l'] = parent_folder
        if name:
            params['action']['name'] = name
        if tags:
            tn = self._return_comma_list(tags)
            params['action']['tn'] = tn
        if view:
            params['action']['view'] = view

        self.request('FolderAction', params)

    def delete_folders(self, paths=None, folder_ids=None, f_type='folder'):
        """
        :param folder_ids: list of ids
        :param path: list of folder's paths
        """
        if folder_ids:
            f_ids = folder_ids
        elif paths:
            f_ids = []
            for path in paths:
                folder = self.get_folder(path=path)
                f_ids.append(folder[f_type]['id'])

        comma_ids = self._return_comma_list(f_ids)

        params = {'action': {
            'id': comma_ids,
            'op': 'delete'
        }}

        self.request('FolderAction', params)

    def get_mountpoint(self, mp_id=None, path=None, uuid=None):
        return self.get_folder(f_id=mp_id, path=path, uuid=uuid)

    def create_mountpoint(self, **kwargs):
        """ Create mountpoint according to attributes definied in soap
        documentation.
        """

        params = {'link': kwargs}

        return self.request('CreateMountpoint', params)['link']

    def delete_mountpoints(self, paths=None, folder_ids=None):
        """
        :param folder_ids: list of ids
        :param path: list of folder's paths
        """
        self.delete_folders(paths=paths, folder_ids=folder_ids, f_type='link')

    def get_folder_grant(self, **kwargs):
        folder = self.get_folder(**kwargs)
        if 'acl' in folder['folder']:
            return folder['folder']['acl']
        else:
            return None

    def modify_folder_grant(
        self,
        folder_ids,
        perm,
        zid=None,
        grantee_name=None,
        gt='usr',
        flags=None
    ):
        """
        :param folder_ids: list of ids
        :param perm: permission to grant to the user on folder(s)
        :param zid: id of user to grant rights
        :param grantee_name: email address of user to grant rights
        :param flags: folder's flags
        """
        f_ids = self._return_comma_list(folder_ids)

        params = {'action': {
            'id': f_ids,
            'op': 'grant',
            'grant': {'perm': perm, 'gt': gt}
        }}

        if perm == 'none':
            params['action']['op'] = '!grant'
            params['action']['zid'] = zid
            # Remove key to raise Zimsoap exception if no zid provided
            if not zid:
                params['action'].pop('zid', None)

        if grantee_name:
            params['action']['grant']['d'] = grantee_name
        elif zid:
            params['action']['grant']['zid'] = zid
        else:
            raise TypeError('missing zid or grantee_name')

        self.request('FolderAction', params)
