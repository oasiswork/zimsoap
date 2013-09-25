#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Zimbra specific objects, they handle parsing and unparsing to/from XML and
# other glue-code.
# Note that they do *not* handle themselves communication with
# zimbra API. It is left to ZimbraAdminClient.

from pysimplesoap.client import SimpleXMLElement
import utils

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
        obj._import_attributes(xml.attributes())

        return obj

    def __init__(self, *args, **kwargs):
        """ By default, import the attributes of kwargs as attributes
        """
        self._import_attributes(kwargs)

    def __eq__(self, other):
        if type(self) != type(other):
            raise TypeError('Cannot compare %s with %s' %\
                                (type(self), type(other)))

        try:
            if not utils.is_zuuid(self.id) or not utils.is_zuuid(other.id):
                raise AttributeError()
        except AttributeError:
            raise ValueError(
                'Both comparees should have a Zimbra UUID as "id" attribute')

        return self.id == other.id

    def __ne__(self, other):
        return not self.__eq__(other)


    def _import_attributes(self, attrdict):
        for k, v in attrdict.items():
            setattr(self, k, str(v))


    def to_xml_selector(self):
        selector = None
        for s in self.SELECTORS:
            if hasattr(self, s):
                selector = s

        if selector is None:
            raise ValueError("At least one %s has to be set as attr."\
                    % str(self.SELECTORS))

        xml = '<%s by="%s" >%s</%s>' %\
            (self.TAG_NAME, selector, getattr(self, selector), self.TAG_NAME)

        return SimpleXMLElement(xml)



class Domain(ZObject):
    """A domain, matching something like:
       <domain id="b37...dfc3ecf6ac" name="sub.domain.tld">
          <a n="zimbraGalLdapPageSize">1000</a>
           ...
       </domain>"""
    TAG_NAME = 'domain'
    SELECTORS = ('id', 'name', 'virtualHostname', 'krb5Realm', 'foreignName')

    def __repr__(self):
        return "<ZimbraDomain:%s>" % self.id

    def __str__(self):
        return "<ZimbraDomain:%s>" % self.name


class ClassOfService(ZObject):
    """ Represents a Class of Service (COS)

    Example:
        <cos id="e00-..a2a" name="default">2</cos>
    """
    TAG_NAME = 'cos'


class Mailbox(ZObject):
    """ Zimbra Mailbox metadata

        <mbox accountId="4cd3...815" changeCheckPoint="5000" contactCount="0"
             groupId="1" id="1" indexVolumeId="2" itemIdCheckPoint="378"
             lastSoapAccess="0" newMessages="63" sizeCheckPoint="140676"
             trackingImap="0" trackingSync="0"
       />
    """
    TAG_NAME = 'mbox'

    def to_xml_selector(self):
        try:
            xml = '<%s id="%s" />' %\
                (self.TAG_NAME, self.id)

        except AttributeError:
            raise ValueError("Mailbox should define attribute \"id\".")


        return SimpleXMLElement(xml)

class DistributionList(ZObject):
    TAG_NAME='dl'
    SELECTORS = ('id', 'name')
