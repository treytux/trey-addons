###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################

from odoo import api, fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    group_id = fields.Many2one(
        comodel_name='account.invoice.line.group',
        string='Line Group',
    )

    @api.multi
    def get_price_unit_by_line(self):
        total = 0.0
        for line in self:
            total += line.price_unit * line.quantity
        return total
