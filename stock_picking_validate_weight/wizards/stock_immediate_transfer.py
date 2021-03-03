##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import api, fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    weight = fields.Float(
        compute='_compute_weight',
        readonly=False,
        store=True,
        string='Total weight',
    )

    @api.depends('pick_ids')
    def _compute_weight(self):
        for wizard in self:
            wizard.weight = (
                wizard.pick_ids[0].shipping_weight
                or wizard.pick_ids[0].weight)

    def process(self):
        for picking in self.pick_ids:
            picking.shipping_weight = self.weight
        return super().process()
