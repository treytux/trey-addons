###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, models


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.model
    def invoice_line_move_line_get(self):
        res = super().invoice_line_move_line_get()
        for line_data in res:
            if 'invl_id' not in line_data:
                continue
            line = self.env['account.invoice.line'].browse(line_data['invl_id'])
            line_data['subvention_id'] = line.subvention_id.id
            line_data['subvention_percent'] = line.subvention_percent
        return res

    @api.model
    def line_get_convert(self, line, part):
        res = super().line_get_convert(line, part)
        res['subvention_id'] = line.get('subvention_id', None)
        res['subvention_percent'] = line.get('subvention_percent', 0)
        return res
