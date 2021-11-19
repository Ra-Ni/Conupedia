from .core import *
import virtuoso.user
import virtuoso.authentication
import virtuoso.course
import virtuoso.namespace

__all__ = [namespace.PREFIX, namespace.SSU, namespace.SSO, namespace.SST, namespace.SSC, 'Session', course.create, user.create, user.get, authentication.get, authentication.create]
