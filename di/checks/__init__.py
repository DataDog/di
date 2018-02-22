from collections import OrderedDict as __OD

from di.utils import DEFAULT_NAME
from .envoy import EnvoyFront
from .nginx import NginxStub

Checks = __OD([
    ('envoy', __OD([
        (DEFAULT_NAME, EnvoyFront),
        (EnvoyFront.flavor, EnvoyFront),
    ])),
    ('nginx', __OD([
        (DEFAULT_NAME, NginxStub),
        (NginxStub.flavor, NginxStub),
    ])),
])
