import json
import sys

import requests


class OdooApi:
    def __init__(self, url):
        self.url = url
        self.session_id = None
        self.session = requests.Session()

    def request(self, endpoint, params):
        headers = {
            'Content-Type': 'application/json',
        }
        if self.session_id:
            headers['X-Openerp-Session-Id'] = self.session_id
        response = self.session.post(
            url='%s%s' % (self.url, endpoint), data=json.dumps(params),
            headers=headers)
        if 'session_id' in self.session.cookies:
            self.session_id = self.session.cookies['session_id']
        response = json.loads(response.content)
        if 'error' in response:
            print('(%s) %s' % (
                response['error']['code'], response['error']['message']))
            print(response['error']['data']['debug'])
            print('-' * 80)
        return response

    def login(self, db, login, password):
        response = self.request(
            '/web/session/authenticate',
            {
                'params': {
                    'db': db,
                    'login': login,
                    'password': password,
                },
            })
        return bool(response)


if __name__ == '__main__':
    oo = OdooApi('http://localhost:8069')
    if not oo.login('bd_test', 'admin', 'admin'):
        print('Login error.')
        sys.exit(-1)
    oo.request(
        '/hr_timesheet/import',
        {
            'enrollment': 12,
            'date': '2024-08-03',
            'incomplete': 'f',
            'signedhoursamount': 8.83,
        }
    )
