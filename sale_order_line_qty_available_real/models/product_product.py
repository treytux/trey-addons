###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.product'

    qty_available_real = fields.Float(
        compute='_compute_qty_available_real',
        digits=dp.get_precision('Product Unit of Measure'),
        string='Real stock',
        store=True,
    )

    @api.depends('qty_available', 'outgoing_qty')
    def _compute_qty_available_real(self):
        for record in self:
            record.qty_available_real = record.qty_available - record.outgoing_qty
