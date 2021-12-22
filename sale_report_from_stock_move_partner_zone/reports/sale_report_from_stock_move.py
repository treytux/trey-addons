###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleReportFromStockMove(models.Model):
    _inherit = 'sale.report.from_stock_move'

    zone_id = fields.Many2one(
        comodel_name='res.partner.zone',
        string='Zone',
        readonly=True,
    )

    def _select(self):
        select = super()._select()
        select += [
            'partner.zone_id as zone_id',
        ]
        return select

    def _group_by(self):
        group = super()._group_by()
        group += [
            'partner.zone_id',
        ]
        return group
