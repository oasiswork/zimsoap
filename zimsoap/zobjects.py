class ZObject(object):
    @classmethod
    def from_xml(cls, xml):
        if not xml.get_name() == cls.TAG_NAME:
            raise TypeError(
                "Class %s should be parsed from XML tag '%s', not '%s'"% \
                    (str(cls), cls.TAG_NAME, xml.get_name()))

        obj = cls()
        # import attributes
        for k, v in xml.attributes().items():
            setattr(obj, k, str(v))

        return obj


class Domain(ZObject):
    """A domain, matching something like:
       <domain id="b37...dfc3ecf6ac" name="sub.domain.tld">
          <a n="zimbraGalLdapPageSize">1000</a>
           ...
       </domain>"""
    TAG_NAME = 'domain'

    def __repr__(self):
        return "<ZimbraDomain:%s>" % self.id

    def __str__(self):
        return "<ZimbraDomain:%s>" % self.name
