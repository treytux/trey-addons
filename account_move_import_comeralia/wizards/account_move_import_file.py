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
            ('payroll_comeralia', 'Payroll from Comeralia'),
        ],
        default='payroll_comeralia',
    )

    def _import_file_payroll_comeralia(self, journal, content):
        def get(line: list, x: int, lenght: int):
            return line[x - 1:][:lenght].strip()

        def format_date(str_date: str):
            try:
                return datetime.strptime(str_date, '%d/%m/%Y').date()
            except Exception:
                return str_date

        self.ensure_one()
        account_obj = self.env['account.account']
        account_move_lines = {}
        return_line = '\r\n' if '\r\n' in content else '\n'
        company_id = self.env.user.company_id.id
        account_640 = self.env.ref(f'l10n_es.{company_id}_account_common_640')
        irpf_tax = self.env.ref(
            f'l10n_es.{company_id}_account_tax_template_p_irpf21t')
        if not irpf_tax:
            raise exceptions.UserError(_(
                'The IRPF tax has not been created, please contact the '
                'administrator.'))
        date = False
        move_type = False
        for line in [ln for ln in content.split(return_line) if ln.strip()]:
            if line.startswith('E'):
                date = format_date(get(line, 2, 10))
                move_type = get(line, 12, 3)
                continue
            if not line.startswith('P'):
                continue
            data = {
                'date': date,
                'account': get(line, 2, 12),
                'type': get(line, 24, 1),
                'amount': float(get(line, 12, 12).replace(',', '.')),
                'employee': get(line, 25, 41),
            }
            account = False
            if account_640.code.startswith(data['account']):
                account = account_640
            if not account:
                account = account_obj.search([
                    ('code', '=like', f'{data["account"]}%%'),
                    ('company_id', '=', self.env.user.company_id.id),
                ], limit=1)
            if not account:
                account = account_obj.search([
                    ('code', '=like', f'{data["account"][:4]}%%'),
                    ('company_id', '=', self.env.user.company_id.id),
                ], limit=1)
            if not account:
                raise exceptions.ValidationError(_(
                    'There is no account that beging by %s or %s.')
                    % (data['account'], data['account'][:4]))
            if len(account) > 1:
                account = account.filtered(lambda a: a.code.endswith('0'))
            if len(account) > 1:
                raise exceptions.ValidationError(_(
                    'With the account code %s I detect several accounting '
                    'accounts %s') % (account.mapped('code'), data['account']))
            partner = False
            analytic_account_id = False
            if move_type == 'NOM':
                employee = self.env['hr.employee'].search([
                    '|',
                    ('name', 'ilike', data['employee']),
                    ('comeralia_name', '=', data['employee']),
                ], limit=1)
                if not employee:
                    raise exceptions.UserError(_(
                        'The employee with the name "%s" does not exist.\n'
                        'As the name sent in the file may be different from '
                        'the one you have in Odoo, you can use the field '
                        '"Name in Comeralia" to put the name that appears in '
                        'the file in the corresponding employee.'
                    ) % data['employee'])
                if not employee.user_id:
                    raise exceptions.ValidationError(_(
                        'Employee "%s" don\'t has user, you must set a user '
                        'in employee form.') % employee.name)
                partner = employee.user_id.partner_id
                if employee.comeralia_project_task_id:
                    analytic_account_id = (
                        employee.comeralia_project_task_id
                        .project_id
                        .analytic_account_id
                        .id
                    )
                if data['amount'] < 0:
                    data['amount'] *= -1
                    data['type'] = 'D' if data['type'] == 'H' else 'H'
                    if employee.comeralia_account_advance_id:
                        account = employee.comeralia_account_advance_id
                        data['account'] = account.code
                if account == account_640 and employee.comeralia_account_id:
                    account = employee.comeralia_account_id
                if account != account_640:
                    analytic_account_id = False
            else:
                partner = self.env.user.company_id.partner_id
            move_line = account_move_lines.setdefault(partner, [])
            move_line.append({
                'account_id': account.id,
                'partner_id': partner.id,
                'name': data['employee'],
                'date': data['date'],
                'debit': data['amount'] if data['type'] == 'D' else 0,
                'credit': data['amount'] if data['type'] == 'H' else 0,
                'analytic_account_id': analytic_account_id,
                'tax_line_id': (
                    irpf_tax.id if account.code.startswith('4751') else False),
                'tax_ids': (
                    [(6, 0, [irpf_tax.id])]
                    if data['type'] == 'D' else False
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
