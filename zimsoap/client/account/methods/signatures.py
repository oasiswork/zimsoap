from zimsoap import zobjects


class MethodMixin:
    def create_signature(self, name, content, contenttype="text/html"):
        """
        :param:  name        verbose name of the signature
        :param:  content     content of the signature, in html or plain-text
        :param:  contenttype can be "text/html" (default) or "text/plain"
        :returns: a zobjects.Signature object
        """
        s = zobjects.Signature(name=name)
        s.set_content(content, contenttype)

        resp = self.request('CreateSignature', {'signature': s.to_creator()})
        return zobjects.Signature.from_dict(resp['signature'])

    def get_signatures(self):
        """ Get all signatures for the current user

        :returns: a list of zobjects.Signature
        """
        signatures = self.request_list('GetSignatures')

        return [zobjects.Signature.from_dict(i) for i in signatures]

    def get_signature(self, signature):
        """Retrieve one signature, discriminated by name or id.

        Note that signature name is not case sensitive.

        :param: a zobjects.Signature describing the signature
               like "Signature(name='my-sig')"

        :returns: a zobjects.Signature object, filled with the signature if no
                 signature is matching, returns None.
        """
        resp = self.request_list('GetSignatures')

        # GetSignature does not allow to filter the results, so we do it by
        # hand...
        if resp and (len(resp) > 0):
            for sig_dict in resp:
                sig = zobjects.Signature.from_dict(sig_dict)
                if hasattr(signature, 'id'):
                    its_this_one = (sig.id == signature.id)
                elif hasattr(signature, 'name'):
                    its_this_one = (sig.name.upper() == signature.name.upper())
                else:
                    raise ValueError('should mention one of id,name')
                if its_this_one:
                    return sig
        else:
            return None

    def delete_signature(self, signature):
        """ Delete a signature by name or id

        :param: signature a Signature object with name or id defined
        """
        self.request('DeleteSignature', {'signature': signature.to_selector()})

    def modify_signature(self, signature):
        """ Modify an existing signature

        Can modify the content, contenttype and name. An unset attribute will
        not delete the attribute but leave it untouched.
        :param: signature a zobject.Signature object, with modified
                         content/contentype/name, the id should be present and
                          valid, the name does not allows to identify the
                         signature for that operation.
        """
        # if no content is specified, just use a selector (id/name)
        dic = signature.to_creator(for_modify=True)

        self.request('ModifySignature', {'signature': dic})
