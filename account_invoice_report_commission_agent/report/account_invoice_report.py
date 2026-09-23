###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AcountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    agents_name = fields.Char(
        string='Agents',
    )

    def _select(self):
        return '%s, move.agents_name as agents_name' % super()._select()
