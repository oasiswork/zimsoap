#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zimbra specific objects, they handle parsing and unparsing to/from XML and
# other glue-code.
# Note that they do *not* handle themselves communication with
# zimbra API. It is left to ZimbraAdminClient.

class ZObject(object):
    """ An abstract class to handle Zimbra Concepts

    A ZObject map to a tag name (subclasses have to define cls.TAG_NAME) :
    A ZObject can be parsed from XML ;
    XML tag attributegs are mapped to ZObject attributes named identically and
    typed to str.
    """
    @classmethod
    def from_xml(cls, xml):
        """ Given a pysimplesoap.SimpleXMLElement, generate a Python Object
        """
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
