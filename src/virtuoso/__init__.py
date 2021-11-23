from . import namespace, user, authentication, course
from virtuoso.core import Session
from virtuoso.user import UserManager
from virtuoso.course import CourseManager
from virtuoso.authentication import Authenticator

__all__ = [
    namespace.PREFIX,
    namespace.SSU,
    namespace.SSO,
    namespace.SST,
    namespace.SSC,
    'Session',
    'UserManager',
    'CourseManager',
    'Authenticator',
    user.create,
    user.get,

]
