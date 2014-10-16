#!/usr/bin/env python
# -*- coding: utf-8 -*-

""" Zimbra specific objects, handle (un)parsing to/from XML and other glue-code.

Note that they do *not* handle themselves communication with
zimbra API. It is left to
ZimbraAdminClient/ZimbraAccountClient/ZimbraMailClient...
"""

import utils

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
    ATTRNAME_PROPERTY='n'

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
            if (k != '_content') and (type(v) in (unicode, str)):
                setattr(self, k, str(v))

    def property(self, property_name, default=Ellipsis):
        """ Returns a property value

        @param default will return that value if the property is not found,
               else, will raise a KeyError.
        """
        try:
            return self._a_tags[property_name]
        except KeyError:
            if default != Ellipsis:
                return default
            else:
                raise



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

        @param dic the dict describing the tag
        @returns   a dict
        """
        props = {}

        if dic.has_key('a'):
            childs = dic['a']
        else:
            childs = []

        for child in childs:
            k = child[cls.ATTRNAME_PROPERTY]
            try:
                v = child['_content']
            except KeyError:
                v = None

            try:
                v = utils.auto_type(str(v))
            except UnicodeEncodeError:
                # Some times, str() fails because of accents...
                v = utils.auto_type(unicode(v))

            if props.has_key(k):
                prev_v = props[k]
                if type(prev_v) != list:
                    props[k] = [prev_v,]

                props[k].append(v)

            else:
                props[k] = v
        return props

    @classmethod
    def _unparse_a_tags(cls, attrs_dict):
        """ Iterates over the dictionary

        @param attrs_dict a dict of attributes
        @returns   a SimpleXMLElement list containing <a> tags
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
            raise ValueError("At least one %s has to be set as attr."\
                    % str(self.SELECTORS))

        val = getattr(self, selector)

        return  {'by': selector,'_content': val}



class Domain(ZObject):
    """A domain, matching something like:
       <domain id="b37...dfc3ecf6ac" name="sub.domain.tld">
          <a n="zimbraGalLdapPageSize">1000</a>
           ...
       </domain>"""
    TAG_NAME = 'domain'
    SELECTORS = ('id', 'name', 'virtualHostname', 'krb5Realm', 'foreignName')


class COS(ZObject):
    TAG_NAME = 'cos'
    SELECTORS = ('id', 'name')

class Server(ZObject):
    """ A Zimbra server object
    """
    TAG_NAME = 'server'
    SELECTORS = ('id', 'name', 'serviceHostname')

class Account(ZObject):
    """An account object
    """
    TAG_NAME = 'account'
    SELECTORS = ('adminName','appAdminName','id',
                 'foreignPrincipal','name','krb5Principal')

    def get_domain(self):
        try:
            domain_name = self.name.split('@')[1]
            return Domain(name=domain_name)
        except AttributeError, e:
            raise NotEnoughInformation(
                'Cannot get domain without self.name filled')

    def get_login_part(self):
        try:
            domain_name = self.name.split('@')[0]
            return Domain(name=domain_name)
        except AttributeError, e:
            raise NotEnoughInformation(
                'Cannot get domain without self.name filled')


    def is_admin(self):
        """ Is it an admin account ?

        No field present means False by default.
        """
        try:
            return self._a_tags['zimbraIsAdminAccount']
        except KeyError:
            return False

    def is_system(self):
        """ Is it a system account ?

        No field present means False by default.
        """
        try:
            return self._a_tags['zimbraIsSystemAccount']
        except KeyError:
            return False

    def is_virtual(self):
        """ Is it a virtual external account ?

        No field present means False by default.
        """
        try:
            return self._a_tags['zimbraIsExternalVirtualAccount']
        except KeyError:
            return False


class Identity(ZObject):
    """An account object
    """
    TAG_NAME = 'identity'
    ATTRNAME_PROPERTY='name'

    def to_creator(self):
        """ Returns the dict suitable for CreateIdentity or ModifyIdentity
        """
        o = {}

        for prop in ('name', 'id'):
            if hasattr(self, prop):
                o[prop] = getattr(self, prop)

        if len(self._a_tags) > 0:
            o['a'] = []
            for node in self._unparse_a_tags(self._a_tags):
                o['a'].append(node)
        return o

    def is_default(self):
        """ Is it the default identity ? """
        # it's not just a convention : default identity name cannot be changed...
        return self.name == 'DEFAULT'


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

    def to_selector(self):
        try:
            return {'id': self.id}
        except AttributeError:
            raise ValueError("Mailbox should define attribute \"id\".")


class DistributionList(ZObject):
    TAG_NAME='dl'
    SELECTORS = ('id', 'name')


class Signature(ZObject):
    TAG_NAME='signature'
    SELECTORS = ('id', 'name')

    @classmethod
    def from_dict(cls, d):
        """ Override default, adding the capture of content and contenttype.
        """
        o = super(Signature, cls).from_dict(d)
        if d.has_key('content'):
        #	Sometimes, several contents, (one txt, other  html), take last
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
                    'too little information on signature, run setContent before')

        return signature

    def get_content(self):
        return self._content

    def has_content(self):
        return (hasattr(self, '_content') and hasattr(self, '_contenttype'))

    def get_content_type(self):
        return self._contenttype


class Task(ZObject):
    TAG_NAME = 'task'
    ATTRNAME_PROPERTY = 'id'

    def to_creator(self, subject, desc):
        """ Return a python-zimbra dict for CreateTaskRequest

        Example :
        <CreateTaskRequest>
            <m su="Task subject">
                <inv>
                    <comp name="Task subject">
                        <fr>Task comment</fr>
                        <desc>Task comment</desc>
                    </comp>
                </inv>
                <mp>
                    <content/>
                </mp>
            </m>
        </CreateTaskRequest>
        """

        task = {
            'm': {
                'su': subject,
                'inv': {
                    'comp': {
                        'name': subject,
                        'fr': {'_content': desc},
                        'desc': {'_content': desc},
                        'percentComplete': '0'
                    }
                },
                'mp': {
                    'content': {}
                }
            }
        }

        return task



