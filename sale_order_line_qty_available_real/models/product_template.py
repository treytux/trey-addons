###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import models, fields, api
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_available_real = fields.Float(
        compute='_compute_qty_available_real',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Stock real')

    @api.one
    @api.depends('qty_available', 'outgoing_qty')
    def _compute_qty_available_real(self):
        self.qty_available_real = sum(
            [p.qty_available_real for p in self.product_variant_ids])
