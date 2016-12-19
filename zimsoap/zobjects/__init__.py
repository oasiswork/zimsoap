#!/usr/bin/env python
# -*- coding: utf-8 -*-
from __future__ import unicode_literals

""" Zimbra specific objects, handle (un)parsing to/from XML and other glue-code

Note that they do *not* handle themselves communication with
zimbra API. It is left to
ZimbraAdminClient/ZimbraAccountClient/ZimbraMailClient...
"""

from zimsoap import utils

__ALL__ = ('admin', 'account', 'mail')


class NotEnoughInformation(Exception):
    """Raised when we try to get information on an object but have too litle
    data to infer it."""
    pass


class ZObject(object):
    """ An abstract class to handle Zimbra Concepts

    A ZObject map to a tag name (subclasses have to define cls.TAG_NAME) :
    A ZObject can be parsed from XML ;
    XML tag attributes are mapped to ZObject attributes named identically and
    typed to str.
    """
    # In <a name="zimbraPrefForwardReply">&gt;</a> it would be 'name'
    ATTRNAME_PROPERTY = 'n'
    SELECTORS = []

    @classmethod
    def from_dict(cls, d):
        """ Given a dict in python-zimbra format or XML, generate
        a Python object.
        """

        if type(d) != dict:
            raise TypeError('Expecting a <dict>, got a {0}'.format(type(d)))
        obj = cls()
        obj._full_data = d

        # import attributes
        obj._import_attributes(d)

        # import <a> child tags as dict items, see __getitem__()
        obj._a_tags = obj._parse_a_tags(d)

        return obj

    def __init__(self, *args, **kwargs):
        """ By default, import the attributes of kwargs as object attributes
        """
        self._import_attributes(kwargs)
        self._a_tags = {}
        self._full_data = {}

    def __hash__(self):
        return hash(str(self))

    def get_full_data(self):
        return self._full_data

    def get_full_xml(self):
        return self._full_data

    def __eq__(self, other):
        if type(self) != type(other):
            raise TypeError('Cannot compare %s with %s' %
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

    def __getitem__(self, k):
        """ Returns an item which is one of the <a> tags (if any). Attributes
        are parsed oportunisticly at the first __getitem__ call.
        """
        return self._a_tags[k]

    def __setitem__(self, k, v):
        self._a_tags[k] = utils.auto_type(v)

    def __repr__(self):
        most_significant_id = getattr(self, 'id',
                                      hex(id(self)))
        return '<%s.%s:%s>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            most_significant_id
            )

    def __str__(self):
        most_significant_id = getattr(self, 'name',
                                      getattr(self, 'id',
                                              hex(id(self))))
        return '<%s.%s:%s>' % (
            self.__class__.__module__,
            self.__class__.__name__,
            most_significant_id
            )

    def _import_attributes(self, dic):
        for k, v in dic.items():
            # We ignore attributes array, they will be handled as properties
            if (k != '_content' and k != 'a'):
                setattr(self, k, v)

    def property(self, property_name, default=Ellipsis):
        """ Returns a property value

        :param: default will return that value if the property is not found,
               else, will raise a KeyError.
        """
        try:
            return self._a_tags[property_name]
        except KeyError:
            if default != Ellipsis:
                return default
            else:
                raise

    def has_property(self, property_name):
        return (property_name in self._a_tags)

    def property_as_list(self, property_name):
        """ property() but encapsulates it in a list, if it's a
        single-element property.
        """
        try:
            res = self._a_tags[property_name]
        except KeyError:
            return []

        if type(res) == list:
            return res
        else:
            return [res]

    @classmethod
    def _parse_a_tags(cls, dic):
        """ Iterates over all <a> tags and builds a dict with those.
        If a tag with same "n" attributes appears several times, the
        dict value is a list with the tags values, else it's a string.

        :param: dic the dict describing the tag
        :returns:   a dict
        """
        props = {}

        if 'a' in dic:
            children = dic['a']
            # If there is only one attribute
            # make it a list anyway for use below
            if not isinstance(children, (list, tuple)):
                children = [children]
        else:
            children = []

        for child in children:
            k = child[cls.ATTRNAME_PROPERTY]
            try:
                v = child['_content']
            except KeyError:
                v = None

            try:
                v = utils.auto_type(str(v))
            except UnicodeEncodeError:
                # Some times, str() fails because of accents...
                v = utils.auto_type(v)

            if k in props:
                prev_v = props[k]
                if type(prev_v) != list:
                    props[k] = [prev_v]

                props[k].append(v)

            else:
                props[k] = v
        return props

    @classmethod
    def _unparse_a_tags(cls, attrs_dict):
        """ Iterates over the dictionary

        :param: attrs_dict a dict of attributes
        :returns:   a SimpleXMLElement list containing <a> tags
        """
        prop_tags = []

        for k, v in attrs_dict.items():
            node = {cls.ATTRNAME_PROPERTY: k, '_content': utils.auto_type(v)}
            prop_tags.append(node)

        return prop_tags

    def to_selector(self):
        selector = None
        for s in self.SELECTORS:
            if hasattr(self, s):
                selector = s

        if selector is None:
            raise ValueError("At least one %s has to be set as attr."
                             % str(self.SELECTORS))

        val = getattr(self, selector)

        return {'by': selector, '_content': val}
