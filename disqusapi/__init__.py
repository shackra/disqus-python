"""
disqus-python
~~~~~~~~~~~~~

disqus = DisqusAPI(api_secret=secret_key)
disqus.trends.listThreads()

"""
try:
    __version__ = __import__('pkg_resources') \
        .get_distribution('disqusapi').version
except Exception:  # pragma: no cover
    __version__ = 'unknown'

import os.path
import warnings
import socket

try:
    import simplejson as json
except ImportError:
    import json

from disqusapi.paginator import Paginator
from disqusapi import compat
from disqusapi.compat import http_client as httplib
from disqusapi.compat import urllib_parse as urllib

__all__ = ['DisqusAPI', 'Paginator']

with open(os.path.join(os.path.dirname(__file__), 'interfaces.json')) as fp:
    INTERFACES = json.load(fp)

HOST = 'disqus.com'


class InterfaceNotDefined(NotImplementedError):
    pass


class APIError(Exception):
    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __str__(self):
        return '%s: %s' % (self.code, self.message)


class InvalidAccessToken(APIError):
    pass

ERROR_MAP = {
    18: InvalidAccessToken,
}


class Result(object):
    def __init__(self, response, cursor=None):
        self.response = response
        self.cursor = cursor or {}

    def __repr__(self):
        return '<%s: %s>' % (self.__class__.__name__, repr(self.response))

    def __iter__(self):
        for r in self.response:
            yield r

    def __len__(self):
        return len(self.response)

    def __getslice__(self, i, j):
        return list.__getslice__(self.response, i, j)

    def __getitem__(self, key):
        return list.__getitem__(self.response, key)

    def __contains__(self, key):
        return list.__contains__(self.response, key)


class Resource(object):
    def __init__(self, api, interface=INTERFACES, node=None, tree=()):
        self.api = api
        self.node = node
        self.interface = interface
        if node:
            tree = tree + (node,)
        self.tree = tree

    def __getattr__(self, attr):
        if attr in getattr(self, '__dict__'):
            return getattr(self, attr)
        interface = self.interface
        if attr not in interface:
            interface[attr] = {}
            # raise InterfaceNotDefined(attr)
        return Resource(self.api, interface[attr], attr, self.tree)

    def __call__(self, **kwargs):
        return self._request(**kwargs)

    def _request(self, **kwargs):
        # Handle undefined interfaces
        resource = self.interface
        for k in resource.get('required', []):
            if k not in (x.split(':')[0] for x in compat.iterkeys(kwargs)):
                raise ValueError('Missing required argument: %s' % k)

        method = kwargs.pop('method', resource.get('method'))

        if not method:
            raise InterfaceNotDefined(
                'Interface is not defined, you must pass ``method`` (HTTP Method).')

        api = self.api

        version = kwargs.pop('version', api.version)
        format = kwargs.pop('format', api.format)

        conn = httplib.HTTPSConnection(HOST, timeout=api.timeout)

        path = '/api/%s/%s.%s' % (version, '/'.join(self.tree), format)

        if 'api_secret' not in kwargs and api.secret_key:
            kwargs['api_secret'] = api.secret_key
        if 'api_public' not in kwargs and api.public_key:
            kwargs['api_key'] = api.public_key

        # We need to ensure this is a list so that
        # multiple values for a key work
        params = []
        for k, v in compat.iteritems(kwargs):
            if isinstance(v, (list, tuple)):
                for val in v:
                    params.append((k, val))
            else:
                params.append((k, v))

        headers = {
            'User-Agent': 'disqus-python/%s' % __version__
        }

        if method == 'GET':
            path = '%s?%s' % (path, urllib.urlencode(params))
            data = ''
        else:
            data = urllib.urlencode(params)

        conn.request(method, path, data, headers)

        response = conn.getresponse()

        # Coerce response to Python
        data = api.formats[format](response.read())

        # Close connection
        conn.close()

        if response.status != 200:
            raise ERROR_MAP.get(data['code'], APIError)(data['code'], data['response'])

        if isinstance(data['response'], list):
            return Result(data['response'], data.get('cursor'))
        return data['response']


class DisqusAPI(Resource):
    formats = {
        'json': json.loads,
    }

    def __init__(self, secret_key=None, public_key=None, format='json', version='3.0',
                 timeout=None, **kwargs):
        self.secret_key = secret_key
        self.public_key = public_key
        if not public_key and not secret_key:
            warnings.warn("You should at least pass ``public_key`` if you don't pass your secret key.")
        self.format = format
        self.version = version
        self.timeout = timeout or socket.getdefaulttimeout()
        super(DisqusAPI, self).__init__(self)

    def _request(self, **kwargs):
        raise SyntaxError('You cannot call the API without a resource.')

    def _get_key(self):
        return self.secret_key
    key = property(_get_key)

    def setSecretKey(self, key):
        self.secret_key = key
    setKey = setSecretKey

    def setPublicKey(self, key):
        self.public_key = key

    def setFormat(self, format):
        self.format = format

    def setVersion(self, version):
        self.version = version

    def setTimeout(self, timeout):
        self.timeout = timeout
