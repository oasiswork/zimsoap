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


class ZObject(object):
    """ An abstract class to handle Zimbra Concepts

    A ZObject map to a tag name (subclasses have to define cls.TAG_NAME) :
    A ZObject can be parsed from XML ;
    XML tag attributes are mapped to ZObject attributes named identically and
    typed to str.
    """
    SELECTORS = []
    PROPERTY_TAG_NAME = 'a'
    # In <a name="zimbraPrefForwardReply">&gt;</a> it would be 'name'
    PROPERTY_NAME_ATTR = 'n'

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
        obj._props = obj._parse_properties(d)

        return obj

    def __init__(self, *args, **kwargs):
        """ By default, import the attributes of kwargs as object attributes
        """
        self._import_attributes(kwargs)
        self._props = {}
        self._full_data = {}

    def __hash__(self):
        return hash(str(self))

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
        return self._props[k]

    def __setitem__(self, k, v):
        self._props[k] = utils.auto_type(v)

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

    def _cast_attribute(self, key, val):
        """ Convenience method for child classes to allow casting attributes
        values when something else than a string is expected

        :param key: the name of the attribute
        :type key: str
        :param val: the value to cast
        :type val: str

        :returns: the casted value
        """
        # By default we raise an Exception to indicate that no specific
        # casting strategy is defined and fall back to utils.auto_type()
        raise NotImplementedError()

    def _import_attributes(self, dic):
        """ Adds top-level dict keys as attributes of the ZObject

        :param dic: the API response dictionnary
        :type dic:  dict
        """
        for k, v in dic.items():
            # We ignore the properties array, it will be handled separately
            if (k != '_content' and k != self.PROPERTY_TAG_NAME):
                try:
                    v = self._cast_attribute(k, v)
                except NotImplementedError:
                    v = utils.auto_type(v)
                setattr(self, k, v)

    @classmethod
    def _cast_property(cls, key, val):
        """ Convenience method for child classes to allow casting properties
        values when something else than a string is expected

        :param key: the name of the property
        :type key: str
        :param val: the value to cast
        :type val: str

        :returns: the casted value
        """
        # By default we raise an Exception to indicate that no specific
        # casting strategy is defined and fall back to utils.auto_type()
        raise NotImplementedError()

    @classmethod
    def _parse_properties(cls, dic):
        """ Iterates over all items of the <PROPERTY_TAG_NAME> element
        and builds a dict with those.

        If a tag with same "PROPERTY_NAME_ATTR" attributes appears several
        times, the value becomes a list with the tag's values,
        otherwise it's a string or another type, as defined by the child class
        in its _cast_property() method or as detected by utils.auto_type().

        :param dic: the API response dictionnary
        :type dic:  dict

        :returns: a dict of properties
        :rtype:   dict
        """
        props = {}

        if cls.PROPERTY_TAG_NAME in dic:
            children = dic[cls.PROPERTY_TAG_NAME]
            # If there is only one attribute
            # make it a list anyway for use below
            if not isinstance(children, (list, tuple)):
                children = [children]
        else:
            children = []

        for child in children:
            k = child[cls.PROPERTY_NAME_ATTR]
            try:
                v = child['_content']
            except KeyError:
                v = None

            try:
                v = cls._cast_property(k, v)
            except NotImplementedError:
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
    def _unparse_properties(cls, attrs_dict):
        """ Iterates over the dictionary

        :param: attrs_dict a dict of attributes
        :returns:   a list of properties ready to be used in a request
        """
        prop_tags = []

        for k, v in attrs_dict.items():
            node = {cls.PROPERTY_NAME_ATTR: k, '_content': utils.auto_type(v)}
            prop_tags.append(node)

        return prop_tags

    def get_full_data(self):
        """ Returns the original API response dictionnary

        :returns: the API response dictionnary
        :rtype:   dict
        """
        return self._full_data

    def has_property(self, name):
        """ Check if the ZObject has a property matching provided name

        :param name: the property name
        :type name:  str

        :returns: True is property exists, False otherwise
        :rtype:   bool
        """
        return (name in self._props)

    def properties(self):
        """ Returns the whole properties dictionnary to make looping easier

        :returns: properties dictionnary
        :rtype:   dict
        """
        return self._props

    def property(self, name, default=Ellipsis):
        """ Returns a property value

        :param name:    the name of the property to get the value for
        :type name:     str
        :param default: a default value if property is not found. If not
                        supplied and the property doesn't exist, a KeyError
                        exception is raised.
        :type default:  any

        :returns: the property's value or default
        """
        try:
            return self._props[name]
        except KeyError:
            if default != Ellipsis:
                return default
            else:
                raise

    def property_as_list(self, name):
        """ Returns a property value but encapsulates it in a list if it's a
        single-element property.

        :param name:    the name of the property to get the value for
        :type name:     str

        :returns: the property's value as a list or an empty list if the
                  property doesn't exist
        :rtype:   list
        """
        try:
            res = self._props[name]
        except KeyError:
            return []

        if type(res) == list:
            return res
        else:
            return [res]

    def to_selector(self):
        """ Returns a dictionary suitable for 'by something' selection
        in requests

        :returns: the selector dictionary
        :rtype:   dict
        """
        selector = None
        for s in self.SELECTORS:
            if hasattr(self, s):
                selector = s

        if selector is None:
            raise ValueError("At least one %s has to be set as attr."
                             % str(self.SELECTORS))

        val = getattr(self, selector)

        return {'by': selector, '_content': val}

    def to_creator(self):
        """ Returns a dict suitable for Create or Modify requests

        :returns: the creator dictionary
        :rtype:   dict
        """
        c = {}

        for attr in self.SELECTORS:
            if hasattr(self, attr):
                c[attr] = getattr(self, attr)

        try:
            if len(self._props) > 0:
                c[self.PROPERTY_TAG_NAME] = []
                for node in self._unparse_properties(self._props):
                    c[self.PROPERTY_TAG_NAME].append(node)
        except AttributeError:
            pass
        return c
