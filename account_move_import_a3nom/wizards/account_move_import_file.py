###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import logging
from datetime import datetime

from odoo import _, exceptions, fields, models

_log = logging.getLogger(__name__)


class AccountMoveImportFile(models.TransientModel):
    _inherit = 'account.move.import_file'

    type = fields.Selection(
        selection_add=[
            ('a3nom', 'A3Nom'),
        ],
        default='a3nom',
    )

    def _import_file_a3nom(self, journal, content):
        def get(line: list, x: int, lenght: int):
            return line[x - 1:][:lenght].strip()

        def format_date(str_date: str):
            try:
                return datetime.strptime(str_date, '%Y%m%d').date()
            except Exception:
                return str_date

        self.ensure_one()
        account_obj = self.env['account.account']
        employee_obj = self.env['hr.employee']
        account_move_lines = {}
        return_line = '\r\n' if '\r\n' in content else '\n'
        company_id = self.env.user.company_id.id
        irpf_tax = self.env.ref(
            f'l10n_es.{company_id}_account_tax_template_p_irpf21t')
        if not irpf_tax:
            raise exceptions.UserError(_(
                'The IRPF tax has not been created, please contact the '
                'administrator.'))
        for line in [ln for ln in content.split(return_line) if ln.strip()]:
            employee_code = get(line, 61, 6)
            if not employee_code:
                raise exceptions.UserError(_(
                    'It seems that the file does not have the identifiers of '
                    'the workers, you have to request a detailed file per '
                    'worker.\n'
                    'The line in the file "%s" has no value for position 61.'
                ) % line)
            data = {
                'company': int(get(line, 2, 5)),
                'date': format_date(get(line, 7, 8)),
                'account': get(line, 16, 12),
                'concept': get(line, 28, 30),
                'type': get(line, 58, 1),
                'amount': float(get(line, 100, 14)),
                'employee': int(employee_code),
            }
            account = account_obj.search([
                ('code', '=like', f'{data["account"]}%%'),
                ('company_id', '=', self.env.user.company_id.id),
            ])
            if not account:
                account = account_obj.search([
                    ('code', '=like', f'{data["account"][:4]}%%'),
                    ('company_id', '=', self.env.user.company_id.id),
                ])
            if not account:
                raise exceptions.ValidationError(_(
                    'There is no account that beging by %s or %s.')
                    % (data['account'], data['account'][:4]))
            account = account.filtered(lambda a: a.code.endswith('0'))
            if len(account) > 1:
                raise exceptions.ValidationError(_(
                    'With the account code %s I detect several accounting '
                    'accounts %s') % (account.mapped('code'), data['account']))
            employee = employee_obj.search([
                ('a3nom_company', '=', data['company']),
                ('a3nom_code', '=', data['employee']),
            ])
            if not employee:
                raise exceptions.ValidationError(_(
                    'Employee with A3 company %s and A3 code %s don\'t exist.')
                    % (data['company'], data['employee']))
            if not employee.filtered(lambda e: e.user_id):
                raise exceptions.ValidationError(_(
                    'Employee with A3 company %s and A3 code %s don\'t has '
                    'user, you must set a user in employee form..')
                    % (data['company'], data['employee']))
            move_line = account_move_lines.setdefault(
                employee.user_id.partner_id, [])
            move_line.append({
                'account_id': account.id,
                'partner_id': employee.user_id.partner_id.id,
                'name': data['concept'],
                'date': data['date'],
                'debit': data['amount'] if data['type'] == 'D' else 0,
                'credit': data['amount'] if data['type'] == 'H' else 0,
                'tax_line_id': (
                    irpf_tax.id if account.code.startswith('4751') else False),
                'tax_ids': (
                    [(6, 0, [irpf_tax.id])]
                    if account.code.startswith('640') else False
                ),
            })
        moves = self.env['account.move'].browse([])
        for partner, lines in account_move_lines.items():
            moves |= moves.create({
                'ref': _('Payroll %s') % partner.name,
                'date': lines[0]['date'],
                'journal_id': journal.id,
                'line_ids': [(0, 0, ln) for ln in lines],
            })
        return moves
