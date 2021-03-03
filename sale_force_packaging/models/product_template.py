###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    force_packaging_qty = fields.Boolean(
        string='Force sell by packaging',
        default=False,
        help='Force sale line quantity to a multiple of package quantity',
    )

    @api.constrains('force_packaging_qty', 'sale_ok')
    def _check_force_packaging_qty_sale_ok(self):
        for product in self:
            if product.force_packaging_qty and not product.sale_ok:
                raise ValidationError(
                    _(
                        'Only products that can be sold can be forced in sale '
                        'order lines.'
                    )
                )

    @api.onchange('sale_ok')
    def _onchange_sale_ok(self):
        if not self.sale_ok and self.force_packaging_qty:
            self.force_packaging_qty = False

    @api.constrains('force_packaging_qty', 'packaging_ids')
    def _check_force_packaging_qty(self):
        for product in self:
            if product.force_packaging_qty:
                if (
                        len(product.product_variant_ids) == 1 and not len(
                        product.packaging_ids) or len(
                        product.product_variant_ids) > 1 and not len(
                        product.product_variant_ids.mapped('packaging_ids'))
                ):
                    raise ValidationError(
                        _(
                            'Only products with packaging can be forced in '
                            'sale order lines.'
                        )
                    )
