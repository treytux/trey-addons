###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    qty_available_real = fields.Float(
        compute='_compute_qty_available_real',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Real stock',
        store=True,
    )

    @api.depends('product_variant_ids.qty_available_real')
    def _compute_qty_available_real(self):
        for record in self:
            record.qty_available_real = sum(
                p.qty_available_real for p in record.product_variant_ids)
