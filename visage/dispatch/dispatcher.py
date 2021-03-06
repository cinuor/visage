"""
this module dispatch the request to backend
"""
import json
from visage.utils.importutils import import_object


class Dispatcher(object):

    def __init__(self, **kwargs):
        """
        :param args: 
        """
        backends = {}

        for key, value in kwargs.items():
            backends[key] = import_object(value)
        self.backends = backends

    def get_backend(self, req):
        return req.get('backend')

    def get_method(self, req):
        return req.get('execute')

    def get_args(self, req):
        empty = tuple()
        try:
            return req.get('args', empty)
        except KeyError:
            return empty

    def get_kwargs(self, req):
        empty = dict()
        try:
            return req.get('kwargs', empty)
        except KeyError:
            return empty

    def __call__(self, msg):
        try:
            request = json.loads(msg)
            backend_name = self.get_backend(request)
            method_name = self.get_method(request)
            args = self.get_args(request)
            kwargs = self.get_kwargs(request)
            print kwargs

            backend = self.backends[backend_name]
            method = getattr(backend, method_name)

            resp = method(*args, **kwargs)
            return resp
        except ValueError as error:
            return str(error)
        except KeyError as error:
            return str(error)


if __name__ == '__main__':

    backends = {
        'Test': 'visage.backend.test.Test'
    }
    j = {
        'backend': 'Test',
        'execute': 'test',
        'args': [],
        'kwargs': {
            'name': 'xxx',
            'id': '123'
        }
    }

    request = json.dumps(j)

    d = Dispatcher(**backends)
    print d(request)
