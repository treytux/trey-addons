###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    subvention_percent = fields.Float(
        string='Subvention (%)',
        track_visibility='onchange',
    )
    subvention_id = fields.Many2one(
        comodel_name='account.subvention',
        string='Subvention',
        track_visibility='onchange',
    )

    def _prepare_invoice_line(self):
        res = super()._prepare_invoice_line()
        res['subvention_id'] = (
            self.subvention_id and self.subvention_id.id or None)
        res['subvention_percent'] = self.subvention_percent
        return res
