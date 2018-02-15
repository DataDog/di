from collections import OrderedDict as __OD

from di.utils import DEFAULT_NAME
from .nginx import NginxStub

Checks = __OD([
    ('nginx', __OD([
        (DEFAULT_NAME, NginxStub),
        ('stub', NginxStub),
    ])),
])
