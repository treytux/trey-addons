# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=80):
        results = super(ProductTemplate, self).name_search(
            name, args=args, operator=operator, limit=limit)
        if not name:
            return results
        info = self.env['product.supplierinfo'].search(
            [('customer_search', 'ilike', name)])
        results += [i.product_tmpl_id.name_get()[0] for i in info]
        return list(set(results))
