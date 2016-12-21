from zimsoap.exceptions import NotEnoughInformation
from zimsoap import utils
from . import ZObject


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


class Server(ZObject):
    """ ServerInfo

    .. code:: xml

        <server name="{name}" id="{id}">
            (<a n="{key}" />)*
         </server>
    """
    TAG_NAME = 'server'
    SELECTORS = ('id', 'name', 'serviceHostname')


class Config(ZObject):
    """A plain ZObject with only properties

    .. code:: xml

        (<a n="{key}" />)*
    """
    TAG_NAME = None


class COS(ZObject):
    """ CosInfo

    .. code:: xml

        <cos id="{id}" name="{name}" [isDefaultCos="{is-default-cos} (0|1)"]>
            (<a [c="{is-cos-attr} (0|1)"]
                [pd="{perm-denied} (0|1)"] n="{key}" />)*
        </cos>
    """
    TAG_NAME = 'cos'
    SELECTORS = ('id', 'name')


class COSCount(ZObject):
    """CosCountInfo

    A custom object with a single attribute 'counters' containing a list of
    (<COS>, int) tuples.
    The request response to work with is as follow:

    .. code:: xml

        (<cos name="{cos-name}" id="{cos-id}">{value} (long)</cos>)*
    """
    TAG_NAME = None

    @classmethod
    def from_dict(cls, d):
        """ Override default to render counters
        as a list of (<COS>, int) tuples.
        """
        o = super(COSCount, cls).from_dict(d)

        o.counters = []
        if 'cos' in d:
            o.counters = [(COS.from_dict(c), int(c['_content']))
                          for c in utils.as_list(d['cos'])]

        return o


class Domain(ZObject):
    """ DomainInfo

    .. code:: xml

       <domain name="{name}" id="{id}">
            (<a n="{key}" />)*
         </domain>
    """
    TAG_NAME = 'domain'
    SELECTORS = ('id', 'name', 'virtualHostname', 'krb5Realm', 'foreignName')

    def is_alias(self):
        """ Check if this domain is an alias domain

        We check the existence of attribute zimbraDomainAliasTargetId for that

        :returns: True if it is an alias domain, False otherwise
        :rtype: bool
        """
        return self.property('zimbraDomainAliasTargetId', None) is not None

    def get_alias_target_name(self):
        """ Get the target domain of an alias domain

        We parse the zimbraMailCatchAllForwardingAddress to extract domain

        :returns: the target domain name or empty string if not an alias domain
        :rtype: str
        """
        prop = str(self.property('zimbraMailCatchAllForwardingAddress', ''))
        if prop:
            return prop[1:]
        else:
            return prop


class Account(AbstractAddressableZObject):
    """AccountInfo

    .. code:: xml

        <account [isExternal="{is-external} (0|1)"] name="{name}" id="{id}">
            (<a n="{key}" />)*
        </account>
    """
    TAG_NAME = 'account'
    SELECTORS = ('adminName', 'appAdminName', 'id',
                 'foreignPrincipal', 'name', 'krb5Principal')

    def is_admin(self):
        """ Is it an admin account ?

        No field present means False by default.
        """
        try:
            return self['zimbraIsAdminAccount']
        except KeyError:
            return False

    def is_system(self):
        """ Is it a system account ?

        No field present means False by default.
        """
        try:
            return self['zimbraIsSystemAccount']
        except KeyError:
            return False

    def is_virtual(self):
        """ Is it a virtual external account ?

        No field present means False by default.
        """
        try:
            return self['zimbraIsExternalVirtualAccount']
        except KeyError:
            return False


class AccountQuota(ZObject):
    """AccountQuotaInfo

    .. code:: xml

         (<account name="{account-name}" id="{account-id}"
                   used="{quota-used-bytes} (long)"
                   limit="{quota-limit-bytes} (long)" />)*
    """
    TAG_NAME = 'account'


class CalendarResource(AbstractAddressableZObject):
    """ CalendarResourceInfo

    .. code:: xml

        <calresource name="{name}" id="{id}">
            (<a n="{key}" />)*
        </calresource>
    """
    TAG_NAME = 'calresource'
    SELECTORS = ('id', 'foreignPrincipal', 'name')

    EQUIPMENT_TYPE = 'Equipment'
    LOCATION_TYPE = 'Location'


class DistributionList(ZObject):
    """ DistributionListInfo

    .. code:: xml

        <dl [dynamic="{dl-is-dynamic} (0|1)"] name="{name}" id="{id}">
            (<dlm>{members} (String)</dlm>)*
            <owners>
                (DistributionListOwner)*
            </owners>
            (<a n="{key}" />)*
         </dl>
    """
    TAG_NAME = 'dl'
    SELECTORS = ('id', 'name')

    @classmethod
    def from_dict(cls, d):
        """ Override default, adding the capture of members and owners.
        """
        owners = []
        if 'owners' in d:
            owners = [DistributionListOwner.fromdict(w)
                      for w in utils.as_list(d['owners'])]
            del d['owners']

        o = super(DistributionList, cls).from_dict(d)

        o.owners = owners

        o.members = []
        if 'dlm' in d:
            o.members = [utils.get_content(member)
                         for member in utils.as_list(d["dlm"])]

        return o


class DistributionListOwner(ZObject):
    """ GranteeInfo

    .. code:: xml

        <owner
            [type="{grantee-type}(usr|grp|egp|all|dom|edom|gst|key|pub|email)"]
            id="{grantee-id}"
            name="{grantee-name}" />
    """
    TAG_NAME = 'owner'


class Mailbox(ZObject):
    """ MailboxWithMailboxId

    .. code:: xml

        <mbox mbxid="{mailbox-id} (int)" [id="{account-id}"]
              [s="{size-in-bytes} (Long)"] />
    """
    TAG_NAME = 'mbox'

    def to_selector(self):
        try:
            return {'id': self.id}
        except AttributeError:
            raise ValueError("Mailbox should define attribute \"id\".")


class MailboxInfo(ZObject):
    """ MailboxInfo

    .. code:: xml

        <mbox id="(int)" groupId="(int)" accountId="..."
              indexVolumeId="(short)" itemIdCheckPoint="(int)"
              contactCount="(int)" sizeCheckPoint="(long)"
              changeCheckPoint="(int)" trackingSync="(int)"
              trackingImap="(0|1)" [lastbackupat="(Integer)"]
              lastSoapAccess="(int)" newMessages="(int)"
        />
    """
    TAG_NAME = 'mbox'


class MailboxStats(ZObject):
    """ MailStats
    
    .. code:: xml

        <stats numMboxes="{num-mailboxes} (long)"
               totalSize="{total-size} (long)" />
    """
    TAG_NAME = 'stats'
