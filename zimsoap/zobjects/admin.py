from . import ZObject, NotEnoughInformation


class Server(ZObject):
    """ A Zimbra server object
    """
    TAG_NAME = 'server'
    SELECTORS = ('id', 'name', 'serviceHostname')


class COS(ZObject):
    """ Represents a Class of Service (COS)

    Example:
        <cos id="e00-..a2a" name="default">2</cos>
    """
    TAG_NAME = 'cos'
    SELECTORS = ('id', 'name')


class Domain(ZObject):
    """A domain, matching something like:
       <domain id="b37...dfc3ecf6ac" name="sub.domain.tld">
          <a n="zimbraGalLdapPageSize">1000</a>
           ...
       </domain>"""
    TAG_NAME = 'domain'
    SELECTORS = ('id', 'name', 'virtualHostname', 'krb5Realm', 'foreignName')

    def get_alias_target_name(self):
        """ The target of a domain is defined in two places :

          - zimbraDomainAliasTargetId: cd330216-ac40-48a2-abe9-812091879714
          - zimbraMailCatchAllForwardingAddress: @zimbratest.example.fr

        Here we parse the zimbraMailCatchAllForwardingAddress to extract domain

        :rtype: str
        """
        prop = str(self.property('zimbraMailCatchAllForwardingAddress', ''))
        if prop:
            return prop[1:]
        else:
            return prop


class QuotaUsage(ZObject):
    TAG_NAME = 'QuotaUsage'
    SELECTORS = ('domain', 'allServers', 'limit', 'offset', 'sortBy',
                 'sortAscending', 'refresh')


class AbstractAddressableZObject(ZObject):
    def get_domain(self):
        try:
            domain_name = self.name.split('@')[1]
            return Domain(name=domain_name)
        except AttributeError:
            raise NotEnoughInformation(
                'Cannot get domain without self.name filled')

    def get_login_part(self):
        try:
            domain_name = self.name.split('@')[0]
            return Domain(name=domain_name)
        except AttributeError:
            raise NotEnoughInformation(
                'Cannot get domain without self.name filled')


class Account(AbstractAddressableZObject):
    """An account object
    """
    TAG_NAME = 'account'
    SELECTORS = ('adminName', 'appAdminName', 'id',
                 'foreignPrincipal', 'name', 'krb5Principal')

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


class CalendarResource(AbstractAddressableZObject):
    """A CalendarResource object
    """
    TAG_NAME = 'calresource'
    SELECTORS = ('id', 'name')

    EQUIPMENT_TYPE = 'Equipment'
    LOCATION_TYPE = 'Location'


class DistributionList(ZObject):
    TAG_NAME = 'dl'
    SELECTORS = ('id', 'name')

    @classmethod
    def from_dict(cls, d):
        """ Override default, adding the capture of members.
        """
        o = super(DistributionList, cls).from_dict(d)
        o.members = []
        if 'dlm' in d:
            o.members = [utils.get_content(member)
                         for member in utils.as_list(d["dlm"])]
        return o


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
