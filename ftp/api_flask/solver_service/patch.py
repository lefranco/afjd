#!/usr/bin/env python3

"""
File : patch.py
This patches a regression in Werkzeug's host validation
Hopefully, temporary !

"""

# pylint: disable=all
# mypy: ignore-errors

import werkzeug.sansio.utils
import werkzeug.wsgi


def patch_werkzeug_host_validation() -> None:
    """Completely disable host validation in Werkzeug"""

    def _bypass_get_host(environ, server_name=None, trusted_hosts=None, extract_forwarded=True):
        """Return host without any validation"""

        # Try to get the real host from various sources
        host = environ.get('HTTP_X_FORWARDED_HOST')
        if not host:
            host = environ.get('HTTP_HOST')
        if not host:
            host = environ.get('SERVER_NAME', 'localhost')
            port = environ.get('SERVER_PORT', '')
            if port and port not in ('80', '443'):
                host = f"{host}:{port}"
        return host

    # Apply the patch
    werkzeug.sansio.utils.get_host = _bypass_get_host
    werkzeug.wsgi.get_host = _bypass_get_host


if __name__ == '__main__':
    assert False, "Do not run this script"
