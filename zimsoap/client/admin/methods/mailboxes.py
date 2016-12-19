from zimsoap import zobjects


class MethodMixin:
    def get_mailbox_stats(self):
        """ Get global stats about mailboxes

        Parses <stats numMboxes="6" totalSize="141077"/>

        :returns: dict with stats
        """
        resp = self.request_single('GetMailboxStats')
        ret = {}
        for k, v in resp.items():
            ret[k] = int(v)

        return ret

    def get_all_mailboxes(self):
        resp = self.request_list('GetAllMailboxes')

        return [zobjects.admin.Mailbox.from_dict(i) for i in resp]
