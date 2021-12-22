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
        return '%s, sub.agents_name as agents_name' % super()._select()

    def _sub_select(self):
        return '%s, ai.agents_name as agents_name' % super()._sub_select()

    def _group_by(self):
        return '%s, ai.agents_name' % super()._group_by()
