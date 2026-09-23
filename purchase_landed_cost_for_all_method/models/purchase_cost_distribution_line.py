###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class PurchaseCostDistributionLine(models.Model):
    _inherit = 'purchase.cost.distribution.line'

    total_weight = fields.Float(
        compute='_compute_total_weight',
        help='The line gross weight in Kg.',
    )
    total_volume = fields.Float(
        compute='_compute_total_volume',
        help='The line volume in litres.',
    )

    @api.multi
    @api.depends('move_id')
    def _compute_standard_price_old(self):
        super()._compute_standard_price_old()
        for line in self:
            line.standard_price_old = (
                line.move_id and line.move_id.price_unit or 0.0)

    @api.multi
    @api.depends('product_id', 'product_qty')
    def _compute_total_volume(self):
        litre_uom = self.env.ref('uom.product_uom_litre')
        for dist_line in self:
            volume_uom = dist_line.product_id.volume_uom_id
            volume_litre = volume_uom._compute_quantity(
                dist_line.product_volume, litre_uom)
            dist_line.total_volume = volume_litre * dist_line.product_qty

    @api.multi
    @api.depends('product_id', 'product_qty')
    def _compute_total_weight(self):
        kg_uom = self.env.ref('uom.product_uom_kgm')
        for dist_line in self:
            weight_uom = dist_line.product_id.weight_uom_id
            weight_kg = weight_uom._compute_quantity(
                dist_line.product_weight, kg_uom)
            dist_line.total_weight = weight_kg * dist_line.product_qty
