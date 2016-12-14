class MethodMixin:
    def add_message(self, msg_content, folder, **kwargs):
        """ Inject a message

        :params string msg_content: The entire message's content.
        :params string folder: Folder pathname (starts with '/') or folder ID
        """
        content = {'m': kwargs}
        content['m']['l'] = str(folder)
        content['m']['content'] = {'_content': msg_content}

        return self.request('AddMsg', content)

    def get_message(self, msg_id, **kwargs):
        content = {'m': kwargs}
        content['m']['id'] = str(msg_id)

        return self.request('GetMsg', content)

    def move_messages(self, ids, folder_id):
        """ Move selected messages to an other folder

        :param msg_ids: list of message's ids to move
        :param folder_id: folder's id where to move messages
        """
        str_ids = self._return_comma_list(ids)
        params = {'action': {
            'id': str_ids,
            'op': 'move',
            'l': folder_id
        }}

        self.request('MsgAction', params)

    def update_messages_flag(self, ids, flag):
        """
        List of flags :
        u -> unread                 f -> flagged
        a -> has attachment         s -> sent by me
        r -> replied                w -> forwarded
        d -> draft                  x -> deleted
        n -> notification sent

        by default a message priority is "normal" otherwise:
        ! -> priority high          ? -> priority low
        """
        str_ids = self._return_comma_list(ids)
        params = {'action': {
            'id': str_ids,
            'op': 'update',
            'f': flag
        }}

        self.request('MsgAction', params)

    def delete_messages(self, ids):
        """ Delete selected messages for the current user

        :param ids: list of ids
        """
        str_ids = self._return_comma_list(ids)
        return self.request('MsgAction', {'action': {'op': 'delete',
                                                     'id': str_ids}})
