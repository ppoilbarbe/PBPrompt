"""Runtime hook: point SSL/requests to the bundled certifi CA bundle."""

import os
import sys

if getattr(sys, "frozen", False):
    _base = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    _cacert = os.path.join(_base, "certifi", "cacert.pem")
    if os.path.isfile(_cacert):
        os.environ.setdefault("SSL_CERT_FILE", _cacert)
        os.environ.setdefault("REQUESTS_CA_BUNDLE", _cacert)
