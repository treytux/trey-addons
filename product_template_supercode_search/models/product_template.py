###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'
    _rec_name = 'supercode'

    supercode = fields.Char(
        string='Supercode',
        store=True,
        compute='_compute_update_supercode',
    )

    @api.multi
    @api.depends(
        'default_code', 'name', 'barcode', 'customer_ids.name.ref',
        'customer_ids.product_code', 'seller_ids.name.ref',
        'seller_ids.product_code')
    def _compute_update_supercode(self):
        for product_tmpl in self:
            val = []
            for supplier in product_tmpl.seller_ids.filtered(lambda s: s.name):
                val += [supplier.name.name, (supplier.name.ref or ''),
                        (supplier.product_code or '')]
            for customer in product_tmpl.customer_ids.filtered(
                    lambda c: c.name):
                val += [customer.name.name, (customer.name.ref or ''),
                        (customer.product_code or '')]
            if product_tmpl.default_code:
                val.append(product_tmpl.default_code)
            if product_tmpl.name:
                val.append(product_tmpl.name)
            if product_tmpl.barcode:
                val.append(product_tmpl.barcode)
            product_tmpl.supercode = ' '.join(val)

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = [('supercode', operator, name)]
        product_tmpls = self.search(domain + args, limit=limit)
        return product_tmpls.name_get()
