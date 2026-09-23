###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    season_id = fields.Many2one(
        comodel_name='product.season',
        string='Season in invoice line',
        readonly=True,
    )

    def _select(self):
        return super(AccountInvoiceReport, self)._select() + \
            ", sub.season_id as season_id"

    def _sub_select(self):
        return super(AccountInvoiceReport, self)._sub_select() + \
            ", ail.season_id as season_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() + \
            ", ail.season_id"
