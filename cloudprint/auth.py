import datetime as dt
import logging
import os
import requests
import shelve
import time

from collections import namedtuple


CodeResponse = namedtuple('CodeResponse',
    ['device_code', 'user_code', 'verification_url', 'expires_at', 'interval'])

class ErrorResponse(Exception): pass


class Auth(object):

    ''' Usage: TODO

    '''

    SCOPE = 'https://www.googleapis.com/auth/cloudprint'

    USER_CODE_URI = 'https://accounts.google.com/o/oauth2/device/code'
    TOKEN_URI = 'https://accounts.google.com/o/oauth2/token'

    GRANT_GET = 'http://oauth.net/grant_type/device/1.0'
    GRANT_REFRESH = 'refresh_token'

    def __init__(self, client_id, client_secret,
            access_token=None, token_type=None, refresh_token=None, expires_at=None):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = access_token
        self.token_type = token_type
        self.refresh_token = refresh_token
        self.expires_at = expires_at

    @classmethod
    def store_creds(cls, path, client_id, client_secret):
        data = shelve.open(path)
        data.clear()
        data.update({'client_id': client_id, 'client_secret': client_secret})
        data.close()

    @classmethod
    def load(cls, path):
        data = shelve.open(path)
        if 'client_id' not in data or 'client_secret' not in data:
            raise RuntimeError('Client ID or Secret is not set in data file')
        obj = cls(**data)
        data.close()
        return obj

    @classmethod
    def clear(cls, path):
        data = shelve.open(path)
        data.clear()
        data.close()

    def save(self, path):
        data = shelve.open(path)
        data.update({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'access_token': self.access_token,
            'token_type': self.token_type,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at
        })
        data.close()

    def is_authenticated(self):
        if self.client_id and self.client_secret and self.access_token and not self.is_expired():
            return True
        return False

    def is_expired(self, when=None):
        when = when or dt.datetime.now()
        return self.expires_at and self.expires_at < when

    def get_code(self):
        resp = requests.post(self.USER_CODE_URI, {'client_id': self.client_id, 'scope': self.SCOPE})

        if resp.status_code != 200:
            raise RuntimeError('invalid response', resp)

        data = resp.json()
        expires_at = dt.datetime.now() + dt.timedelta(seconds=data['expires_in'])

        return CodeResponse(device_code=data['device_code'], user_code=data['user_code'],
            verification_url=data['verification_url'], expires_at=expires_at, interval=data['interval'])

    def get_token(self, device_code):
        data = {
            'code': device_code,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': self.GRANT_GET,
        }
        resp = requests.post(self.TOKEN_URI, data)

        data = resp.json()
        if 'error' in data:
            raise ErrorResponse(data['error'])

        self.access_token = data['access_token']
        self.token_type = data['token_type']
        self.refresh_token = data['refresh_token']
        self.expires_at = dt.datetime.now() + dt.timedelta(seconds=data['expires_in'])

    def refresh_token(self):
        data = {
            'refresh_token': token['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET,
            'grant_type': GRANT_REFRESH,
        }
        resp = requests.post(TOKEN_URI, data)

        data = resp.json()
        if 'error' in data:
            raise ErrorResponse(data['error'])

        self.access_token = data['access_token']
        self.token_type = data['token_type']
        self.refresh_token = data['refresh_token']
        self.expires_at = dt.datetime.now() + dt.timedelta(seconds=data['expires_in'])



def authenticate():
    token = load_token()
    if 'access_token' not in token:
        data = get_user_code()
        webbrowser.open(data['verification_url'])
        print('Verification code: %s' % data['user_code'])

        data = get_token(data['device_code'], data['interval'])

        token = save_token(token['access_token'], token['refresh_token'],
            dt.datetime.now() + dt.timedelta(seconds=token['expires_in']))

        print('Access token: %s' % token['access_token'])
        print('Refresh token: %s' % token['refresh_token'])

    elif token['expires_at'] <= dt.datetime.now():
        print('Token needs refresh')
        token = refresh_token()
        token = save_token(token['access_token'], token['refresh_token'],
            dt.datetime.now() + dt.timedelta(seconds=token['expires_in']))

    else:
        print('Valid token found')
