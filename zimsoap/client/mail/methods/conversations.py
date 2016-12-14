class MethodMixin:
    def get_conversation(self, conv_id, **kwargs):
        content = {'c': kwargs}
        content['c']['id'] = int(conv_id)

        return self.request('GetConv', content)

    def delete_conversations(self, ids):
        """ Delete selected conversations

        :params ids: list of ids
        """

        str_ids = self._return_comma_list(ids)
        self.request('ConvAction', {'action': {'op': 'delete',
                                               'id': str_ids
                                               }})

    def move_conversations(self, ids, folder):
        """ Move selected conversations to an other folder

        :params ids: list of ids
        :params folder: folder id
        """

        str_ids = self._return_comma_list(ids)
        self.request('ConvAction', {'action': {'op': 'move',
                                               'id': str_ids,
                                               'l': str(folder)}})
