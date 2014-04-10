import os.path
import collections
import json
import mimetypes
import requests


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
            result.append(Printer(self, data['id'], data['name'], data['description'], data['status']))
        return result

    def get_printer(self, printer_id):
        printer_idx = printer_id.isdigit() and int(printer_id) or None
        printers = self.list_printers()
        for ii in range(len(printers)):
            if (printer_idx and ii == printer_idx) or printers[ii].id == printer_id:
                return printers[ii]
        raise RuntimeError('No such printer')


class Printer(object):

    def __init__(self, client, printer_id, name, description, status):
        self.client = client
        self.id = printer_id
        self.name = name
        self.description = description
        self.status = status

    def list_jobs(self):
        raise NotImplementedError

    def cancel_job(self, job_id):
        raise NotImplementedError

    def submit_job(self, filename, fileobj=None):
        data = {
            'printerid': self.id,
            'title': os.path.basename(filename),
            'ticket': '{"version": "1.0", "print": {}}',
        }
        content = fileobj or open(filename, 'rb')
        files = {
            'content': content,
        }
        resp = self.client.post(self.client.CLOUDPRINT_URL + '/submit', data=data, files=files)
        if not fileobj:
            content.close()

        rdata = resp.json()
        if not rdata.get('success'):
            raise RuntimeError(rdata['message'])

        return rdata['job']['id']
