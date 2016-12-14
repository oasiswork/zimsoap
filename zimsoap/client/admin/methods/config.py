class MethodMixin:
    def get_all_config(self):
        resp = self.request_list('GetAllConfig')
        config = {}
        for attr in resp:
            # If there is multiple attributes with the same name
            if attr['n'] in config:
                if isinstance(config[attr['n']], str):
                    config[attr['n']] = [config[attr['n']], attr['_content']]
                else:
                    config[attr['n']].append(attr['_content'])
            else:
                config[attr['n']] = attr['_content']
        return config

    def get_config(self, attr):
        resp = self.request_list('GetConfig', {'a': {'n': attr}})
        if len(resp) > 1:
            config = {attr: []}
            for a in resp:
                config[attr].append(a['_content'])
        elif len(resp) == 1:
            config = {attr: resp[0]['_content']}
        else:
            raise KeyError('{} not found'.format(attr))
        return config

    def modify_config(self, attr, value):
        self.request('ModifyConfig', {
            'a': {
                'n': attr,
                '_content': value
            }})
        if attr[0] == '-' or attr[0] == '+':
            attr = attr[1::]
        return self.get_config(attr)
