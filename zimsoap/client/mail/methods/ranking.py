class MethodMixin:
    def reset_ranking(self):
        """Reset the contact ranking table for the account
        """
        self.request('RankingAction', {'action': {'op': 'reset'}})

    def delete_ranking(self, email):
        """Delete a specific address in the auto-completion of the users

        :param email: the address to remove
        """
        self.request('RankingAction', {'action': {'op': 'reset',
                                                  'email': email
                                                  }})
