# <COPYRIGHT_TAG>

VERSION_MAJOR = "23"
VERSION_MINOR = "07"
VERSION_PATCH = "0"
VERSION_EXTRA = "rc0"

__version__ = "%s.%s.%s" % (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH)

if VERSION_EXTRA:
    __version__ = "%s-%s" % (__version__, VERSION_EXTRA)


def dts_version():
    """
    Return the version of dts package
    """
    return __version__


__all__ = ["dts_version", "__version__"]
