from zimsoap import zobjects


class MethodMixin:
    def get_all_mailboxes(self):
        """ Fetches info for all Mailboxes

        :returns: a list os MailboxInfo
        :rtype:   [zobjects.admin.MailboxInfo]
        """
        return self.request_list(
            'GetAllMailboxes', {}, zobjects.admin.MailboxInfo)

    def get_account_mailbox(self, account_id):
        """ Returns the Mailbox matching an account ID.

        Usefull to get the size (attribute 's'), and the mailbox ID.
        Returns nothing appart from that.

        :param account_id: the Zimbra ID of the account we want the mailbox for
        :type account_id:  int

        :returns: the account's mailbox object
        :rtype:   zobjects.admin.Mailbox or None
        """
        selector = zobjects.admin.Mailbox(id=account_id).to_selector()
        return self.request_single(
            'GetMailbox', {'mbox': selector}, zobjects.admin.Mailbox)

    def get_mailbox_stats(self):
        """ Get global stats about mailboxes

        :returns: a MailboxStats objects with the stats as attributes
        :rtype:   zobjects.admin.MailboxStats
        """
        return self.request_single(
            'GetMailboxStats', {}, zobjects.admin.MailboxStats)
