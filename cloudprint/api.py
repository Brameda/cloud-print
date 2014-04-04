import collections
import requests


Printer = collections.namedtuple('Printer', ['id', 'name', 'description', 'status'])


class ErrorResponse(Exception): pass



class Client(object):

    CLOUDPRINT_URL = "https://www.google.com/cloudprint"

    def __init__(self, auth):
        self.auth = auth

    def get(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).update({'Authorization': 'Bearer ' + self.auth.access_token})
        return requests.get(*args, **kwargs)

    def post(self, *args, **kwargs):
        kwargs.setdefault('headers', {}).update({'Authorization': 'Bearer ' + self.auth.access_token})
        return requests.post(*args, **kwargs)

    def list_printers(self):
        resp = self.get(self.CLOUDPRINT_URL + '/search')
        if resp.status_code != requests.codes.ok:
            raise ErrorResponse

        result = []
        for data in resp.json()['printers']:
            result.append(Printer(data['id'], data['name'], data['description'], data['status']))

