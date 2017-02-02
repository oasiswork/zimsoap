from . import ZObject


class Identity(ZObject):
    """An identity object
    """
    SELECTORS = ('name', 'id')
    TAG_NAME = 'identity'
    ATTRNAME_PROPERTY = 'name'

    def is_default(self):
        """ Is it the default identity ? """
        # it's not just a convention : default identity name cannot be
        # changed...
        return self.name == 'DEFAULT'

    def to_selector(self):
        """ For some reason, the selector for <identity> is

            <identity id="1234" />

        rather than

            <identity by="id"></identity>
        """

        for i in self.SELECTORS:
            if hasattr(self, i):
                val = getattr(self, i)
                selector = i
                break

        return {selector: val}


class Signature(ZObject):
    TAG_NAME = 'signature'
    SELECTORS = ('id', 'name')

    @classmethod
    def from_dict(cls, d):
        """ Override default, adding the capture of content and contenttype.
        """
        o = super(Signature, cls).from_dict(d)
        if 'content' in d:
            # Sometimes, several contents, (one txt, other  html), take last
            try:
                o._content = d['content']['_content']
                o._contenttype = d['content']['type']
            except TypeError:
                o._content = d['content'][-1]['_content']
                o._contenttype = d['content'][-1]['type']

        return o

    def to_selector(self):
        """ For some reason, the selector for <signature> is

            <signature id="1234" />

        rather than

            <signature by="id"></signature>
        """

        for i in self.SELECTORS:
            if hasattr(self, i):
                val = getattr(self, i)
                selector = i
                break

        return {selector: val}

    def get_content(self):
        return self._content

    def set_content(self, content, contenttype='text/html'):
        self._content = content
        self._contenttype = contenttype

    def to_creator(self, for_modify=False):
        """ Returns a dict object suitable for a 'CreateSignature'.

        A signature object for creation is like :

            <signature name="unittest">
              <content type="text/plain">My signature content</content>
            </signature>

        which is :

            {
             'name' : 'unittest',
             'content': {
               'type': 'text/plain',
               '_content': 'My signature content'
             }
            }

        Note that if the contenttype is text/plain, the content with text/html
        will be cleared by the request (for consistency).
        """
        signature = {}

        if for_modify:
            try:
                # we should have an ID
                signature['id'] = self.id
            except AttributeError:
                raise AttributeError('a modify request should specify an ID')
            # Case where we change or set a name
            if hasattr(self, 'name'):
                signature['name'] = self.name

        else:
            # a new signature should have a name
            signature['name'] = self.name

        if self.has_content():
            # Set one, flush the other (otherwise, we let relief behind...)
            if self._contenttype == 'text/plain':
                plain_text = self._content
                html_text = ''
            else:
                html_text = self._content
                plain_text = ''

            content_plain = {'type': 'text/plain', '_content': plain_text}
            content_html = {'type': 'text/html', '_content': html_text}

            signature['content'] = [content_plain, content_html]

        else:
            # A creation request should have a content
            if not for_modify:
                raise AttributeError(
                    'too little information on signature, '
                    'run setContent before')

        return signature

    def has_content(self):
        return (hasattr(self, '_content') and hasattr(self, '_contenttype'))

    def get_content_type(self):
        return self._contenttype
