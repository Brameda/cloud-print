import os
import time
import webbrowser

from argparse import ArgumentParser

from . import auth

parser = ArgumentParser()
subparsers = parser.add_subparsers()

auth_parser = subparsers.add_parser('auth', help='authentication')
auth_subparsers = auth_parser.add_subparsers()

AUTH_DATA = os.path.expanduser('~/.cloudprint')


def auth_login(args):
    try:
        authobj = auth.Auth.load(AUTH_DATA)
    except RuntimeError:
        print('Set credentials first')
        return

    if authobj.is_authenticated():
        print('Already authenticated')
        return

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
            authobj.save(AUTH_DATA)
            break

auth_login_parser = auth_subparsers.add_parser('login')
auth_login_parser.set_defaults(call=auth_login)


def auth_refresh(args):
    try:
        authobj = auth.Auth.load(AUTH_DATA)
    except RuntimeError:
        print('Set credentials first')
        return

    if not authobj.is_authenticated():
        print('Not authenticated')
        return
    elif not authobj.is_expired():
        print('Token is not expired')
        return

    authobj.refresh()
    authobj.save(AUTH_DATA)

auth_refresh_parser = auth_subparsers.add_parser('refresh')
auth_refresh_parser.set_defaults(call=auth_refresh)


def auth_clear(args):
    if args.yes:
        auth.Auth.clear(AUTH_DATA)
    else:
        print('use --yes key to confirm')

auth_clear_parser = auth_subparsers.add_parser('clear')
auth_clear_parser.add_argument('--yes', action='store_true', default=False)
auth_clear_parser.set_defaults(call=auth_clear)


def auth_setcreds(args):
    auth.Auth.store_creds(AUTH_DATA, args.client_id, args.client_secret)

auth_setcreds_parser = auth_subparsers.add_parser('setcreds')
auth_setcreds_parser.add_argument('client_id')
auth_setcreds_parser.add_argument('client_secret')
auth_setcreds_parser.set_defaults(call=auth_setcreds)


def auth_status(args):
    authobj = auth.Auth.load(AUTH_DATA)
    if authobj.client_id and authobj.client_secret:
        print('Client ID:     %s' % authobj.client_id)
        print('Client Secret: %s' % authobj.client_secret)

        if authobj.is_authenticated():
            print('Access token:  %s (%s)' % (authobj.access_token, ('expired' if authobj.is_expired() else 'valid')))
            print('Refresh token: %s' % authobj.refresh_token)
        else:
            print('Not authenticated')

    else:
        print('Please set client id/secret')


auth_status_parser = auth_subparsers.add_parser('status')
auth_status_parser.set_defaults(call=auth_status)


def main():
    args = parser.parse_args()
    args.call(args)

if __name__ == '__main__':
    main()
