###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    purchase_last_price = fields.Float(
        string='Purchase last price',
        digits=dp.get_precision('Product Price'),
        readonly=True,
        compute='_compute_purchase_last_price',
        copy=False,
    )
    margin_purchase_last_price = fields.Float(
        string='Margin on purchase last price (%)',
        compute='_compute_margin_purchase_last_price',
        copy=False,
    )

    @api.depends(
        'product_variant_ids', 'product_variant_ids.purchase_last_price')
    def _compute_purchase_last_price(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.purchase_last_price = (
                    template.product_variant_ids.purchase_last_price)

    @api.depends(
        'product_variant_ids', 'product_variant_ids.margin_purchase_last_price',
        'product_variant_ids.purchase_last_price')
    def _compute_margin_purchase_last_price(self):
        for template in self:
            if len(template.product_variant_ids) == 1:
                template.margin_purchase_last_price = (
                    template.product_variant_ids.margin_purchase_last_price)
