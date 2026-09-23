###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class PurchaseReport(models.Model):
    _inherit = 'purchase.report'

    qty_received = fields.Float(
        string='Qty Received',
        readonly=True,
    )
    qty_invoiced = fields.Float(
        string='Qty Invoiced',
        readonly=True,
    )
    order_id = fields.Many2one(
        comodel_name='purchase.order',
        string='Order #',
        readonly=True,
    )

    def _select(self):
        select = super()._select()
        select += """
            , sum(l.qty_received/u.factor*u2.factor) as qty_received
            , sum(l.qty_invoiced/u.factor*u2.factor) as qty_invoiced
            , s.id as order_id
        """
        return select

    def _group_by(self):
        group = super()._group_by()
        group += """
            , l.qty_received
            , l.qty_invoiced
            , s.id
        """
        return group
