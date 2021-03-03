##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from odoo import api, fields, models


class StockImmediateTransfer(models.TransientModel):
    _inherit = 'stock.immediate.transfer'

    carrier_id = fields.Many2one(
        comodel_name='delivery.carrier',
        compute='_compute_carrier',
        readonly=False,
        store=True,
        string='Carrier',
    )

    @api.depends('pick_ids')
    def _compute_carrier(self):
        for wizard in self:
            wizard.carrier_id = wizard.pick_ids[0].carrier_id.id

    def process(self):
        for picking in self.pick_ids:
            picking.carrier_id = self.carrier_id.id
        return super().process()
