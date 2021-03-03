###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    price = fields.Float(
        compute='_compute_price',
        inverse='_set_price',
        store=False,
    )
    ref_price = fields.Float(
        string='Reference price',
        default=0.0,
        digits=dp.get_precision('Product Price'),
        required=True,
        help='The price to purchase a product',
    )

    def _set_price(self):
        if self._context.get('no_update_ref_price'):
            return
        for supplierinfo in self:
            supplierinfo.ref_price = supplierinfo.price

    @api.depends('ref_price', 'name.supplier_pricelist_id')
    def _compute_price(self):
        assert not (len(self) > 1 and 'force_price' in self._context), \
            'Not is possible force price to more than one supplierinfo record'
        for supplierinfo in self:
            ref_price = self._context.get(
                'force_price', supplierinfo.ref_price)
            supplierinfo.price = ref_price
