import os
import time
import webbrowser

from argparse import ArgumentParser
from functools import wraps

from . import auth, api

parser = ArgumentParser()
subparsers = parser.add_subparsers()


class Error(RuntimeError): pass


auth_parser = subparsers.add_parser('auth', help='authentication')
auth_subparsers = auth_parser.add_subparsers()

AUTH_DATA = os.path.expanduser('~/.cloudprint')


def auth_login(args):
    authobj = auth.AuthShelve(AUTH_DATA)

    if authobj.is_authenticated():
        raise Error('Already authenticated')
    elif not authobj.client_id or not authobj.client_secret:
        raise Error('Set credentials first')

    code = authobj.get_code()
    webbrowser.open(code.verification_url)

    print('\n\nVerification code: %s\n\n' % code.user_code)

    while True:
        try:
            authobj.get_token(code.device_code)
        except auth.ErrorResponse:
            time.sleep(code.interval)
            print('...retry')
        else:
            print('Authenticated successfully')
            authobj.save()
            break

auth_login_parser = auth_subparsers.add_parser('login')
auth_login_parser.set_defaults(call=auth_login)


def auth_refresh(args):
    authobj = auth.AuthShelve(AUTH_DATA)

    if not authobj.is_authenticated():
        raise Error('Not authenticated')
    elif not authobj.is_expired() and not args.force:
        raise Error('Token is not expired')

    authobj.refresh()
    authobj.save()

auth_refresh_parser = auth_subparsers.add_parser('refresh')
auth_refresh_parser.add_argument('--force', action='store_true', default=False)
auth_refresh_parser.set_defaults(call=auth_refresh)


def auth_clear(args):
    authobj = auth.AuthShelve(AUTH_DATA)
    if args.yes:
        authobj.clear()
        authobj.save()
    else:
        print('use --yes key to confirm')

auth_clear_parser = auth_subparsers.add_parser('clear')
auth_clear_parser.add_argument('--yes', action='store_true', default=False)
auth_clear_parser.set_defaults(call=auth_clear)


def auth_setcreds(args):
    authobj = auth.AuthShelve(AUTH_DATA)
    authobj.set_credentials(args.client_id, args.client_secret)
    authobj.save()


auth_setcreds_parser = auth_subparsers.add_parser('setcreds')
auth_setcreds_parser.add_argument('client_id')
auth_setcreds_parser.add_argument('client_secret')
auth_setcreds_parser.set_defaults(call=auth_setcreds)


def auth_status(args):
    authobj = auth.AuthShelve(AUTH_DATA)
    if authobj.client_id and authobj.client_secret:
        print('Client ID:     %s' % authobj.client_id)
        print('Client Secret: %s' % authobj.client_secret)

        if authobj.is_authenticated():
            print('Access token:  %s (%s)' % (authobj.access_token, ('expired' if authobj.is_expired() else 'valid')))
            print('Refresh token: %s' % authobj.refresh_token)
        else:
            raise Error('Not authenticated')

    else:
        print('Please set client id/secret')


auth_status_parser = auth_subparsers.add_parser('status')
auth_status_parser.set_defaults(call=auth_status)


def apicall(func):
    @wraps(func)
    def wrapper(args):
        authobj = auth.AuthShelve(AUTH_DATA)
        if not authobj.is_authenticated():
            raise Error('Not authenticated')
        return func(args, api.Client(authobj))
    return wrapper


@apicall
def printers_list(args, client):
    printers = client.list_printers()
    for ii in range(len(printers)):
        print('%d %s %s' % (ii, printers[ii].name, printers[ii].status))

printers_parser = subparsers.add_parser('printers', help='list printers')
printers_parser.set_defaults(call=printers_list)


@apicall
def submit_job(args, client):
    printer = client.get_printer(args.printer_id)
    try:
        printer.submit_job(args.filename)
    except FileNotFoundError:
        raise Error('File not found')

submit_parser = subparsers.add_parser('submit', help='submit job to printer')
submit_parser.add_argument('printer_id')
submit_parser.add_argument('filename')
submit_parser.set_defaults(call=submit_job)


def main():
    args = parser.parse_args()

    try:
        args.call(args)
    except RuntimeError as exc:
        print(exc)

if __name__ == '__main__':
    main()
