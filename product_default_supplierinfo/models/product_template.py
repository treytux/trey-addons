# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def create(self, vals):
        res = super(ProductTemplate, self).create(vals)
        self.env['product.supplierinfo'].create({
            'product_tmpl_id': res.id,
            'company_id': self.env.user.company_id.id,
            'pricelist_ids': [(0, 0, {'min_quantity': 1, 'price': 0.})],
            'name': self.env.user.company_id.default_supplier_id.id})
        return res
