###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import json

import requests
from odoo import _, fields, models
from odoo.exceptions import ValidationError


class AccountJournal(models.Model):
    _inherit = 'account.journal'

    cashdro_host = fields.Char(
        string='Cashdro IP',
        copy=False,
    )
    cashdro_user = fields.Char(
        string='Cashdro user',
        copy=False,
    )
    cashdro_password = fields.Char(
        string='Cashdro password',
        copy=False,
    )
    cashdro_posid = fields.Char(
        string='Cashdro point of sale id',
        copy=False,
    )
    cashdro_posuser = fields.Char(
        string='Cashdro point of sale user',
        copy=False,
    )

    def http_get(self, operation, args=None):
        journal = self.env['account.journal'].browse(
            self.env.context['journal_id'])
        url = 'https://%s/Cashdro3WS/index.php?operation=%s' % (
            journal.cashdro_host, operation)
        for key, value in args.items() or {}:
            if isinstance(value, dict):
                value = json.dumps(value)
            url += f'&{key}={value}'
        response = requests.get(url, verify=False)
        if response.status_code != 200:
            raise ValidationError(
                _('[CASHDRO] Operation error to call %s: %s') % (
                    url, response.status_code))
        return json.loads(response.content)

    def start_operation(self):
        amount = self.env.context['sale_amount']
        journal = self.env['account.journal'].browse(
            self.env.context['journal_id'])
        amount = round(amount * 100, 2)
        response = self.http_get('startOperation', {
            'name': journal.cashdro_user,
            'password': journal.cashdro_password,
            'posid': journal.cashdro_posid,
            'posuser': journal.cashdro_posuser,
            'type': 4,
            'parameters': {'amount': int(amount)},
        })
        if response['code'] != 1:
            return response
        operation_id = response['data']
        response = self.http_get('acknowledgeOperationId', {
            'name': journal.cashdro_user,
            'password': journal.cashdro_password,
            'operationId': operation_id,
        })
        if response['code'] != 1:
            return response
        response['data'] = operation_id
        return response

    def finish_operation(self):
        operation_id = self.env.context['operation_id']
        journal = self.env['account.journal'].browse(
            self.env.context['journal_id'])
        return self.http_get('finishOperation', {
            'name': journal.cashdro_user,
            'password': journal.cashdro_password,
            'posid': journal.cashdro_posid,
            'posuser': journal.cashdro_posuser,
            'type': 2,
            'operationId': operation_id,
        })

    def ask_operation(self):
        operation_id = self.env.context['operation_id']
        journal = self.env['account.journal'].browse(
            self.env.context['journal_id'])
        return self.http_get('askOperation', {
            'name': journal.cashdro_user,
            'password': journal.cashdro_password,
            'posid': journal.cashdro_posid,
            'posuser': journal.cashdro_posuser,
            'type': 2,
            'operationId': operation_id,
        })

    def check_cashdro_config(self):
        return all([
            self.cashdro_user, self.cashdro_password, self.cashdro_posuser,
            self.cashdro_posid, self.cashdro_host])
