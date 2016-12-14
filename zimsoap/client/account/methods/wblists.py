class MethodMixin:
    def get_white_black_lists(self):
        return self.request('GetWhiteBlackList')

    def add_to_blacklist(self, values):
        param = {'blackList': {'addr': []}}
        for value in values:
            param['blackList']['addr'].append({'op': '+', '_content': value})

        self.request('ModifyWhiteBlackList', param)

    def remove_from_blacklist(self, values):
        param = {'blackList': {'addr': []}}
        for value in values:
            param['blackList']['addr'].append({'op': '-', '_content': value})

        self.request('ModifyWhiteBlackList', param)

    def add_to_whitelist(self, values):
        param = {'whiteList': {'addr': []}}
        for value in values:
            param['whiteList']['addr'].append({'op': '+', '_content': value})

        self.request('ModifyWhiteBlackList', param)

    def remove_from_whitelist(self, values):
        param = {'whiteList': {'addr': []}}
        for value in values:
            param['whiteList']['addr'].append({'op': '-', '_content': value})

        self.request('ModifyWhiteBlackList', param)
