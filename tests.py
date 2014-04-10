import datetime as dt
from unittest.mock import patch
from nose.tools import assert_raises
from cloudprint import auth, api


def test_is_authenticated():
    assert auth.Auth('client_id', 'client_secret').is_authenticated() is False
    assert auth.Auth('client_id', 'client_secret', 'access_token').is_authenticated() is True

def test_is_expired():
    assert auth.Auth('client_id', 'client_secret',
        expires_at=dt.datetime(2001, 1, 1, 0, 0, 1)).is_expired(dt.datetime(2001, 1, 1, 0, 0, 0)) is False
    assert auth.Auth('client_id', 'client_secret',
        expires_at=dt.datetime(2001, 1, 1, 0, 0, 0)).is_expired(dt.datetime(2001, 1, 1, 0, 0, 1)) is True


def test_get_code_success():
    with patch('requests.post') as Response:
        resp = Response.return_value
        resp.status_code = 200
        resp.json.return_value = {
            "device_code": "device_code",
            "user_code": "a9xfwk9c",
            "verification_url": "http://www.google.com/device",
            "expires_in": 1800,
            "interval": 5
        }

        code = auth.Auth('client_id', 'client_secret').get_code()
        assert isinstance(code, auth.CodeResponse)
        assert code.device_code == 'device_code'


def test_get_code_failure_on_400():
    with patch('requests.post') as Response:
        resp = Response.return_value
        resp.status_code = 400

        obj = auth.Auth('client_id', 'client_secret')
        assert_raises(RuntimeError, obj.get_code)


def test_get_token_success():
    with patch('requests.post') as Response:
        resp = Response.return_value
        resp.status_code = 200
        resp.json.return_value = {
            "access_token": "access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
            "refresh_token": "refresh_token"
        }
        obj = auth.Auth('client_id', 'client_secret')
        obj.get_token('device_code')

        assert obj.access_token == 'access_token'
        assert obj.token_type == 'Bearer'
        assert obj.refresh_token == 'refresh_token'

        assert obj.expires_at > dt.datetime.now()
        assert obj.expires_at <= dt.datetime.now() + dt.timedelta(hours=1)


def test_get_token_error():
    with patch('requests.post') as Response:
        resp = Response.return_value
        resp.status_code = 403
        resp.json.return_value = {
            "error": "error message",
        }
        obj = auth.Auth('client_id', 'client_secret')
        assert_raises(auth.ErrorResponse, obj.get_token, 'device_code')


def test_refresh_success():
    with patch('requests.post') as Response:
        resp = Response.return_value
        resp.status_code = 200
        resp.json.return_value = {
            "access_token": "refreshed_access_token",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        obj = auth.Auth('client_id', 'client_secret', 'access_token',
            'token_type', 'refresh_token', dt.datetime(2001, 1, 1, 0, 0, 0))
        obj.refresh()

        assert obj.access_token == 'refreshed_access_token'
        assert obj.token_type == 'Bearer'
        assert obj.refresh_token == 'refresh_token'

        assert obj.expires_at > dt.datetime.now()
        assert obj.expires_at <= dt.datetime.now() + dt.timedelta(hours=1)


def test_refresh_failure():
    with patch('requests.post') as Response:
        resp = Response.return_value
        resp.status_code = 403
        resp.json.return_value = {
            "error": "error message",
        }
        obj = auth.Auth('client_id', 'client_secret', 'access_token',
            'token_type', 'refresh_token', dt.datetime(2001, 1, 1, 0, 0, 0))
        assert_raises(auth.ErrorResponse, obj.refresh)


def test_list_printers():
    with patch('requests.get') as Response:
        resp = Response.return_value
        resp.status_code = 200
        resp.json.return_value = {
            'printers': [
                {'id': 'id1', 'name': 'name1', 'description': 'description1', 'status': 'status1'},
                {'id': 'id2', 'name': 'name2', 'description': 'description2', 'status': 'status2'},
            ]
        }
        client = api.Client(auth.Auth('client_id', 'client_secret', 'access_token',
            'token_type', 'refresh_token', dt.datetime(3000, 1, 1, 0, 0, 0)))
        printers = client.list_printers()

        assert (printers[0].id, printers[0].name, printers[0].description) == ('id1', 'name1', 'description1')
        assert (printers[1].id, printers[1].name, printers[1].description) == ('id2', 'name2', 'description2')


def test_get_printer_by_id():
    with patch('requests.get') as Response:
        resp = Response.return_value
        resp.status_code = 200
        resp.json.return_value = {
            'printers': [
                {'id': 'id1', 'name': 'name1', 'description': 'description1', 'status': 'status1'},
                {'id': 'id2', 'name': 'name2', 'description': 'description2', 'status': 'status2'},
            ]
        }
        client = api.Client(auth.Auth('client_id', 'client_secret', 'access_token',
            'token_type', 'refresh_token', dt.datetime(3000, 1, 1, 0, 0, 0)))

        printer = client.get_printer('id1')
        assert (printer.id, printer.name, printer.description) == ('id1', 'name1', 'description1')


def test_get_printer_by_index():
    with patch('requests.get') as Response:
        resp = Response.return_value
        resp.status_code = 200
        resp.json.return_value = {
            'printers': [
                {'id': 'id1', 'name': 'name1', 'description': 'description1', 'status': 'status1'},
                {'id': 'id2', 'name': 'name2', 'description': 'description2', 'status': 'status2'},
            ]
        }
        client = api.Client(auth.Auth('client_id', 'client_secret', 'access_token',
            'token_type', 'refresh_token', dt.datetime(3000, 1, 1, 0, 0, 0)))
        printer = client.get_printer(0)

        assert (printer.id, printer.name, printer.description) == ('id1', 'name1', 'description1')
