from zimsoap import zobjects
from zimsoap.exceptions import ZimSOAPException


class MethodMixin:
    def add_filter_rule(
            self, name, condition, filters, actions, active=1, way='in'):
        """
        :param: name filter name
        :param: condition allof or anyof
        :param: filters dict of filters
        :param: actions dict of actions
        :param: way string discribing if filter is for 'in' or 'out' messages
        :returns: list of user's zobjects.FilterRule
        """

        filters['condition'] = condition

        new_rule = {
            'name': name,
            'active': active,
            'filterTests': filters,
            'filterActions': actions
        }

        new_rules = [zobjects.mail.FilterRule.from_dict(new_rule)]

        prev_rules = self.get_filter_rules(way=way)

        # if there is already some rules
        if prev_rules:
            for rule in prev_rules:
                # don't add rule if it already exist
                if rule.name == new_rules[0].name:
                    raise ZimSOAPException(
                        'filter %s already exists' % rule.name)
            new_rules = new_rules + prev_rules

        content = {
            'filterRules': {
                'filterRule': [r._full_data for r in new_rules]
            }
        }
        if way == 'in':
            self.request('ModifyFilterRules', content)
        elif way == 'out':
            self.request('ModifyOutgoingFilterRules', content)
        return new_rules

    def get_filter_rule(self, _filter, way='in'):
        """ Return the filter rule

        :param: _filter a zobjects.FilterRule or the filter name
        :param: way string discribing if filter is for 'in' or 'out' messages
        :returns: a zobjects.FilterRule"""
        if isinstance(_filter, zobjects.mail.FilterRule):
            _filter = _filter.name
        for f in self.get_filter_rules(way=way):
            if f.name == _filter:
                return f
        return None

    def get_filter_rules(self, way='in'):
        """
        :param: way string discribing if filter is for 'in' or 'out' messages
        :returns: list of zobjects.FilterRule
        """
        try:
            if way == 'in':
                filters = self.request(
                    'GetFilterRules')['filterRules']['filterRule']
            elif way == 'out':
                filters = self.request(
                    'GetOutgoingFilterRules')['filterRules']['filterRule']

            # Zimbra return a dict if there is only one instance
            if isinstance(filters, dict):
                filters = [filters]

            return [zobjects.mail.FilterRule.from_dict(f) for f in filters]
        except KeyError:
            return []

    def apply_filter_rule(self, _filter, query='in:inbox', way='in'):
        """
        :param: _filter _filter a zobjects.FilterRule or the filter name
        :param: query on what will the filter be applied
        :param: way string discribing if filter is for 'in' or 'out' messages
        :returns: list of impacted message's ids
        """
        if isinstance(_filter, zobjects.mail.FilterRule):
            _filter = _filter.name

        content = {
            'filterRules': {
                'filterRule': {'name': _filter}
                },
            'query': {'_content': query}
        }
        if way == 'in':
            ids = self.request('ApplyFilterRules', content)
        elif way == 'out':
            ids = self.request('ApplyOutgoingFilterRules', content)

        if ids:
            return [int(m) for m in ids['m']['ids'].split(',')]
        else:
            return []

    def delete_filter_rule(self, _filter, way='in'):
        """ delete a filter rule

        :param: _filter a zobjects.FilterRule or the filter name
        :param: way string discribing if filter is for 'in' or 'out' messages
        :returns: a list of zobjects.FilterRule
        """
        updated_rules = []
        rules = self.get_filter_rules(way=way)

        if isinstance(_filter, zobjects.mail.FilterRule):
            _filter = _filter.name

        if rules:
            for rule in rules:
                if not rule.name == _filter:
                    updated_rules.append(rule)

        if rules != updated_rules:
            content = {
                'filterRules': {
                    'filterRule': [f._full_data for f in updated_rules]
                }
            }
            if way == 'in':
                self.request('ModifyFilterRules', content)
            elif way == 'out':
                self.request('ModifyOutgoingFilterRules', content)

        return updated_rules
