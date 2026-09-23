###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class StockBackorderConfirmation(models.TransientModel):
    _inherit = 'stock.backorder.confirmation'

    weight = fields.Float(
        compute='_compute_weight',
        readonly=False,
        store=True,
        string='Total weight',
    )

    @api.depends('pick_ids')
    def _compute_weight(self):
        for wizard in self:
            wizard.weight = sum([
                line.product_id.weight * line.quantity_done
                for line in wizard.pick_ids[0].move_ids])

    def process(self):
        context = self.env.context.copy()
        context['weight'] = self.weight
        self.env.context = context
        res = super().process()
        for picking in self.pick_ids:
            picking.shipping_weight_validate = self.weight
            picking.shipping_weight = self.weight
        return res

    def process_cancel_backorder(self):
        context = self.env.context.copy()
        context['weight'] = self.weight
        self.env.context = context
        res = super().process_cancel_backorder()
        for picking in self.pick_ids:
            picking.shipping_weight_validate = self.weight
            picking.shipping_weight = self.weight
        return res
