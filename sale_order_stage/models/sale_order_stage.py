###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import fields, models


class SaleOrderStage(models.Model):
    _name = 'sale.order.stage'
    _description = 'Sale Order Stage'
    _order = 'sequence, name'

    name = fields.Char(
        string='Name',
        required=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    sale_count = fields.Integer(
        string='Sale Count',
        compute='_compute_sale_count',
    )

    def _compute_sale_count(self):
        for stage in self:
            stage.sale_count = self.env['sale.order'].search_count(
                [('stage_id', '=', stage.id)])

    def action_view_sales(self):
        self.ensure_one()
        action = self.env.ref('sale.action_orders').read()[0]
        action['domain'] = [('stage_id', '=', self.id)]
        return action
