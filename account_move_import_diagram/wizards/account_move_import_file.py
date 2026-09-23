###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
import base64
from datetime import datetime

import xlrd
from odoo import _, exceptions, fields, models


class AccountMoveImportFile(models.TransientModel):
    _inherit = 'account.move.import_file'

    type = fields.Selection(
        selection_add=[
            ('diagram', 'Diagram'),
        ],
        default='diagram',
        ondelete={
            'diagram': 'set default',
        },
    )

    def get_file_content(self):
        self.ensure_one()
        if self.type != 'diagram':
            return super().get_file_content()
        try:
            return xlrd.open_workbook(
                file_contents=base64.b64decode(self.file))
        except Exception as e:
            raise exceptions.ValidationError(_(
                'Error reading Excel file: %s') % str(e))

    def _import_file_diagram(self, journal, content):
        def format_date(str_date):
            try:
                return datetime.strptime(str(str_date), '%d.%m.%Y').date()
            except Exception:
                return str_date

        def get_cell_value(sheet, row_idx, col_idx):
            try:
                value = sheet.cell_value(row_idx, col_idx)
                return str(value).strip()
            except IndexError:
                return False

        def get_cell_float(sheet, row_idx, col_idx):
            try:
                value = sheet.cell_value(row_idx, col_idx)
                return float(value)
            except (IndexError, ValueError):
                return 0.0

        def get_account(code):
            return self.env.ref(
                f'l10n_es.{self.env.company.id}_account_common_{code}')

        self.ensure_one()
        irpf_tax = self.env.ref(
            f'l10n_es.{self.env.company.id}_account_tax_template_p_irpf21t')
        if not irpf_tax:
            raise exceptions.ValidationError(_(
                'The IRPF tax has not been created, please contact the '
                'administrator.'))
        moves = self.env['account.move'].browse([]).with_context(
            skip_invoice_sync=True, check_move_validity=False)
        sheet = content.sheet_by_index(0)
        move_date = format_date(get_cell_value(sheet, 0, 4).split(' ')[-1:][0])
        for row_idx in range(sheet.nrows):
            code = get_cell_value(sheet, row_idx, 0)
            if not code:
                continue
            if code == 'Código':
                continue
            employee_vat = get_cell_value(sheet, row_idx, 2)
            employee_name = get_cell_value(sheet, row_idx, 1)
            employee = self.env['hr.employee'].search([
                '|',
                ('identification_id', '=', employee_vat),
                ('user_id.partner_id.vat', '=', employee_vat),
            ])
            if not employee:
                raise exceptions.ValidationError(_(
                    'Employee "%s" not found. I search by the VAT of the '
                    'user contact or the identification ID of the employee '
                    'record. Please check that this data is filled in or that '
                    'there is one for VAT %s.'
                ) % (employee_name, employee_vat))
            if not employee.user_id or not employee.user_id.partner_id:
                raise exceptions.ValidationError(_(
                    'The employee "%s" must have a user linked with a '
                    'contact associated with the user.') % employee.name)
            partner = employee.user_id.partner_id
            gross = get_cell_float(sheet, row_idx, 6)
            benefit = get_cell_float(sheet, row_idx, 4)
            amount_640 = gross - benefit
            move_lines = []
            if amount_640 > 0:
                move_lines.append({
                    'account_id': get_account('640').id,
                    'partner_id': partner.id,
                    'name': employee_name,
                    'date': move_date,
                    'debit': amount_640,
                    'credit': 0,
                    'tax_ids': [(6, 0, [irpf_tax.id])],
                    'tax_tag_ids': [
                        (6, 0, [self.env.ref('l10n_es.mod_111_02').id])],
                })
            if benefit > 0:
                move_lines.append({
                    'account_id': get_account('471').id,
                    'partner_id': partner.id,
                    'name': employee_name,
                    'date': move_date,
                    'debit': benefit,
                    'credit': 0,
                })
            move_lines += [
                {
                    'account_id': get_account('642').id,
                    'partner_id': partner.id,
                    'name': employee_name,
                    'date': move_date,
                    'debit': get_cell_float(sheet, row_idx, 13),
                    'credit': 0,
                },
                {
                    'account_id': get_account('4751').id,
                    'partner_id': partner.id,
                    'name': employee_name,
                    'date': move_date,
                    'debit': 0,
                    'credit': get_cell_float(sheet, row_idx, 9),
                    'tax_line_id': irpf_tax.id,
                    'tax_repartition_line_id': (
                        irpf_tax.invoice_repartition_line_ids.filtered(
                            lambda x: x.repartition_type == 'tax'
                        ).id
                    ),
                },
                {
                    'account_id': get_account('476').id,
                    'partner_id': partner.id,
                    'name': employee_name,
                    'date': move_date,
                    'debit': 0,
                    'credit': get_cell_float(sheet, row_idx, 11),
                },
                {
                    'account_id': get_account('476').id,
                    'partner_id': partner.id,
                    'name': employee_name,
                    'date': move_date,
                    'debit': 0,
                    'credit': get_cell_float(sheet, row_idx, 13),
                },
                {
                    'account_id': get_account('465').id,
                    'partner_id': partner.id,
                    'name': employee_name,
                    'date': move_date,
                    'debit': 0,
                    'credit': get_cell_float(sheet, row_idx, 12),
                },
            ]
            moves |= moves.create({
                'ref': _('Payroll %s') % employee.name,
                'partner_id': partner.id,
                'date': move_lines[0]['date'],
                'journal_id': journal.id,
                'line_ids': [(0, 0, ln) for ln in move_lines],
            })
        return moves
