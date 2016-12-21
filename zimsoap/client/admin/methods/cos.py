from zimsoap import zobjects


class MethodMixin:
    def get_all_cos(self):
        """ Fetches the information for all COS

        :returns: a list of COS objects
        :rtype:   [zobjects.admin.COS]
        """
        return self.request_list('GetAllCos', {}, zobjects.admin.COS)

    def get_cos(self, cos):
        """ Fetches the information for a COS

        :param cos: the COS object to be used as selector
        :type cos:  zobjects.admin.COS

        :returns: a COS object with the COS information
        :rtype:   zobjects.admin.COS
        """
        return self.request_single(
            'GetCos', {'cos': cos.to_selector()}, zobjects.admin.COS)

    def get_account_cos(self, account):
        """ Fetch the cos for a given account

        Quite different from the original request which returns COS + various
        URL + zimbraMailHost... But all other informations are accessible
        through get_account.

        :param account: the Zimbra account we want the COS for
        :type account:  zobjects.admin.Account

        :returns: a COS object
        :rtype:   zobjects.admin.COS or None
        """
        return self.request_single(
            'GetAccountInfo', {'account': account.to_selector()},
            zobjects.admin.COS)

    def count_account(self, domain=None):
        """ Counts the number of accounts sorted by COS, possibly limited
        to a specific domain

        :param domain: the domain to use as a selector
        :type domain:  zobjects.admin.Domain

        :returns: a COSCount object
                  with COS ids as properties and counts as values
        :rtype:   zobjects.admin.COSCount
        """
        params = {}
        if domain is not None:
            params['domain'] = domain.to_selector()

        return self.request_single(
            'CountAccount', params, zobjects.admin.COSCount)
