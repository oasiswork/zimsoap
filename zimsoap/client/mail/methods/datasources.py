class MethodMixin:
    def create_data_source(self, data_source, dest_folder):
        """ Create data source from a dict
        data_source example =
        {
            'pop3': {
                'leaveOnServer': "(0|1)", 'id': 'data-source-id',
                'name': 'data-source-name',
                'isEnabled': '(0|1)', 'importOnly': '(0|1)',
                'host': 'data-source-server', 'port': 'data-source-port',
                'connectionType': '(cleartext|ssl|tls|tls_is_available)',
                'username': 'data-source-username',
                'password': 'data-source-password',
                'emailAddress': 'data-source-address',
                'useAddressForForwardReply': '(0|1)',
                'defaultSignature': 'default-signature-id',
                'forwardReplySignature': 'forward-reply-signature-id',
                'fromDisplay': 'data-source-from-display',
                'replyToAddress': 'data-source-replyto-address',
                'replyToDisplay': 'data-source-replyto-display',
                'importClass': 'data-import-class',
                'failingSince': 'data-source-failing-since'
            }
        }
        """
        folder = self.create_folder(dest_folder)
        for type_source, source_config in data_source.items():
            data_source[type_source]['l'] = folder['id']
        return self.request('CreateDataSource', data_source)

    def get_data_sources(self, types=[], source_addresses=[], source_id=None):
        all_data_sources = self.request('GetDataSources')

        data_sources = {}
        if types and source_addresses:
            for t in types:
                data_sources = {t: []}
                if t in all_data_sources and isinstance(all_data_sources[t],
                                                        list):
                    for data_source in all_data_sources[t]:
                        if data_source['emailAddress'] in source_addresses:
                            data_sources[t].append(data_source)
                elif t in all_data_sources and isinstance(all_data_sources[t],
                                                          dict):
                    if all_data_sources[t]['emailAddress'] in source_addresses:
                        data_sources[t].append(all_data_sources[t])

        elif types and not source_addresses:
            for t in types:
                data_sources = {t: []}
                if t in all_data_sources and isinstance(all_data_sources[t],
                                                        list):
                    for data_source in all_data_sources[t]:
                        data_sources[t].append(data_source)
                elif t in all_data_sources and isinstance(all_data_sources[t],
                                                          dict):
                    data_sources[t].append(all_data_sources[t])

        elif source_addresses and not types:
            for t in all_data_sources.keys():
                if isinstance(all_data_sources[t], list):
                    for data_source in all_data_sources[t]:
                        if data_source['emailAddress'] in source_addresses:
                            try:
                                data_sources[t].append(data_source)
                            except KeyError:
                                data_sources = {t: []}
                                data_sources[t].append(data_source)
                elif isinstance(all_data_sources[t], dict):
                    if all_data_sources[t]['emailAddress'] in source_addresses:
                        try:
                            data_sources[t].append(all_data_sources[t])
                        except KeyError:
                            data_sources = {t: []}
                            data_sources[t].append(all_data_sources[t])

        elif source_id:
            for t in all_data_sources.keys():
                data_sources = {t: []}
                if isinstance(all_data_sources[t], list):
                    for data_source in all_data_sources[t]:
                        if data_source['id'] == source_id:
                            data_sources[t].append(data_source)
                elif isinstance(all_data_sources[t], dict):
                    if all_data_sources[t]['id'] == source_id:
                        data_sources[t].append(all_data_sources[t])

        else:
            return all_data_sources

        return data_sources

    def modify_data_source(self, data_source):
        """ Modify data source from a dict
        data_source example =
        {
            'pop3': {
                'leaveOnServer': "(0|1)", 'id': 'data-source-id',
                'name': 'data-source-name', 'l': 'data-source-folder-id',
                'isEnabled': '(0|1)', 'importOnly': '(0|1)',
                'host': 'data-source-server', 'port': 'data-source-port',
                'connectionType': '(cleartext|ssl|tls|tls_is_available)',
                'username': 'data-source-username',
                'password': 'data-source-password',
                'emailAddress': 'data-source-address',
                'useAddressForForwardReply': '(0|1)',
                'defaultSignature': 'default-signature-id',
                'forwardReplySignature': 'forward-reply-signature-id',
                'fromDisplay': 'data-source-from-display',
                'replyToAddress': 'data-source-replyto-address',
                'replyToDisplay': 'data-source-replyto-display',
                'importClass': 'data-import-class',
                'failingSince': 'data-source-failing-since'
            }
        }
        """
        return self.request('ModifyDataSource', data_source)

    def delete_data_source(self, data_source):
        """
        Delete data source with it's name or ID.
        data_source = { 'imap': {'name': 'data-source-name'}}
        or
        data_source = { 'pop3': {'id': 'data-source-id'}}
        """
        source_type = [k for k in data_source.keys()][0]
        complete_source = self.get_data_sources(
            source_id=data_source[source_type]['id'])
        folder_id = complete_source[source_type][0]['l']
        self.delete_folders(folder_ids=[folder_id])
        return self.request('DeleteDataSource', data_source)
