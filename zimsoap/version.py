from distutils.version import StrictVersion


class Version(object):
    """Version of the package"""

    def __setattr__(self, *args):
        raise TypeError("can't modify immutable instance")
    __delattr__ = __setattr__

    def __init__(self, num):
        super(Version, self).__setattr__('release', num)

    @property
    def version(self):
        return '.'.join(self.release.split('.')[:2])

    @property
    def major(self):
        return self.release.split('.')[0]

    @property
    def minor(self):
        return self.release.split('.')[1]

    @property
    def patch(self):
        return self.release.split('.')[2]

    def __eq__(self, other):
        return (
            not StrictVersion(self.release) < StrictVersion(other.release) and
            not StrictVersion(other.release) < StrictVersion(self.release))

    def __ne__(self, other):
        return (
            StrictVersion(self.release) < StrictVersion(other.release) or
            StrictVersion(other.release) < StrictVersion(self.release))

    def __gt__(self, other):
        return StrictVersion(other.release) < StrictVersion(self.release)

    def __ge__(self, other):
        return not StrictVersion(self.release) < StrictVersion(other.release)

    def __le__(self, other):
        return not StrictVersion(other.release) < StrictVersion(self.release)
