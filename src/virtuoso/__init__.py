from . import namespace, user, authentication, course
from .core import Session

__all__ = [
    namespace.PREFIX,
    namespace.SSU,
    namespace.SSO,
    namespace.SST,
    namespace.SSC,
    'Session',
    user.create,
    user.get,
    authentication.get,
    authentication.create,
    course.get,
    course.rating,
    course.add_rating,
    course.remove_rating,
    course.mark,
    course.recommend,
    course.popular,
    course.latest,
    course.explore,
]
