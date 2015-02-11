import zimsoap.client
import zimsoap.utils
from zimsoap.zobjects import *


zc = zimsoap.client.ZimbraAdminClient("xxxxxxx", "7071")
zc.login("zimbra", "xxxxxxxxxx")
a = zc.get_distribution_list(DistributionList(name="testliste@zimbralab.example.org"))

try:
    liste = zc.delete_distribution_list(DistributionList(name="testliste@zimbralab.example.org"))
except Exception, e:
    print e

liste = zc.create_distribution_list("testliste@zimbralab.example.org")
zc.add_distribution_list_member(DistributionList(name="testliste@zimbralab.example.org"),
                                ["test1@example.com", "test2@example.com", "test3@example.com"])
a = zc.get_distribution_list(DistributionList(name="testliste@zimbralab.example.org"))
zc.remove_distribution_list_member(DistributionList(name="testliste@zimbralab.example.org"), ["test2@example.com"])
b = zc.get_distribution_list(DistributionList(name="testliste@zimbralab.example.org"))
zc.add_distribution_list_member(DistributionList(name="testliste@zimbralab.example.org"),
                                ["test21@example.com", "test22@example.com", "test23@example.com"])
c = zc.get_distribution_list(DistributionList(name="testliste@zimbralab.example.org"))
print c.members
