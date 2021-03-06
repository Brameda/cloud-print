import datetime as dt
import requests
import shelve

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

    def is_authenticated(self):
        if self.client_id and self.client_secret and self.access_token:
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

    def refresh(self):
        data = {
            'refresh_token': self.refresh_token,
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'grant_type': self.GRANT_REFRESH,
        }
        resp = requests.post(self.TOKEN_URI, data)

        data = resp.json()
        if 'error' in data:
            raise ErrorResponse(data['error'])

        self.access_token = data['access_token']
        self.token_type = data['token_type']
        self.expires_at = dt.datetime.now() + dt.timedelta(seconds=data['expires_in'])


class AuthShelve(Auth):

    def __init__(self, path):
        self.datafile_path = path
        data = shelve.open(self.datafile_path)
        super(AuthShelve, self).__init__(data.get('client_id'), data.get('client_secret'),
            data.get('access_token'), data.get('token_type'), data.get('refresh_token'), data.get('expires_at'))
        data.close()

    def set_credentials(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_type = None
        self.refresh_token = None
        self.expires_at = None

    def clear(self):
        self.set_credentials(None, None)

    def save(self):
        data = shelve.open(self.datafile_path)
        data.update({
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'access_token': self.access_token,
            'token_type': self.token_type,
            'refresh_token': self.refresh_token,
            'expires_at': self.expires_at
        })
        data.close()
