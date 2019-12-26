###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    partner_state_id = fields.Many2one(
        comodel_name='res.country.state',
        string='Customer State',
    )

    def _select(self):
        select_str = super(SaleReport, self)._select()
        select_str += ', partner.state_id as partner_state_id'
        return select_str

    def _group_by(self):
        group_by_str = super(SaleReport, self)._group_by()
        group_by_str += ', partner.state_id'
        return group_by_str
