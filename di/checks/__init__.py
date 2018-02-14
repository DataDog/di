from collections import OrderedDict as __OD

from .nginx import NginxStub

Checks = __OD([
    ('nginx', __OD([
        ('default', NginxStub),
        ('stub', NginxStub),
    ])),
])
