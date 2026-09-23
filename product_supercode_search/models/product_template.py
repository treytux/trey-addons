###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    supercode = fields.Char(
        string='Supercode',
        store=True,
        compute='_compute_supercode',
    )

    @api.depends(
        'name',
        'product_variant_ids.default_code',
        'product_variant_ids.barcode',
        'seller_ids.product_code',
        'seller_ids.partner_id.name',
        'seller_ids.partner_id.ref',
        'customer_ids.product_code',
        'customer_ids.partner_id.name',
        'customer_ids.partner_id.ref',
    )
    def _compute_supercode(self):
        for template in self:
            values = []
            if template.name:
                values.append(template.name)
            for variant in template.product_variant_ids:
                if variant.default_code:
                    values.append(variant.default_code)
                if variant.barcode:
                    values.append(variant.barcode)
            for seller in template.seller_ids.filtered('partner_id'):
                values += [
                    seller.partner_id.name,
                    seller.partner_id.ref or '',
                    seller.product_code or '',
                ]
            for customer in template.customer_ids.filtered('partner_id'):
                values += [
                    customer.partner_id.name,
                    customer.partner_id.ref or '',
                    customer.product_code or '',
                ]
            template.supercode = ' '.join(v for v in values if v)
