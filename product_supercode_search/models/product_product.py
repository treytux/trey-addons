###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductProduct(models.Model):
    _inherit = 'product.product'

    supercode = fields.Char(
        string='Supercode',
        store=True,
        compute='_compute_supercode',
    )

    @api.depends(
        'product_tmpl_id.supercode',
        'default_code',
        'barcode',
        'seller_ids.product_code',
        'seller_ids.partner_id.name',
        'seller_ids.partner_id.ref',
        'customer_ids.product_code',
        'customer_ids.partner_id.name',
        'customer_ids.partner_id.ref',
    )
    def _compute_supercode(self):
        for product in self:
            values = []
            if product.product_tmpl_id.supercode:
                values.append(product.product_tmpl_id.supercode)
            if product.default_code:
                values.append(product.default_code)
            if product.barcode:
                values.append(product.barcode)
            sellers = product.seller_ids.filtered(
                lambda s: s.product_id == product and s.partner_id)
            for seller in sellers:
                values += [
                    seller.partner_id.name,
                    seller.partner_id.ref or '',
                    seller.product_code or '',
                ]
            customers = product.customer_ids.filtered(
                lambda c: c.product_id == product and c.partner_id)
            for customer in customers:
                values += [
                    customer.partner_id.name,
                    customer.partner_id.ref or '',
                    customer.product_code or '',
                ]
            product.supercode = ' '.join(v for v in values if v)
