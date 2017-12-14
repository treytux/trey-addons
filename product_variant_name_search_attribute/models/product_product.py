# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductProduct(models.Model):
    _inherit = "product.product"

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=80):
        if not args:
            args = []
        separator = self.env['ir.config_parameter'].get_param(
            'product.variant.name.search.separator')
        name_splited = [part.strip() for part in name.split(separator)]
        if not len(name_splited) > 1:
            return super(ProductProduct, self).name_search(
                name, args=args, operator=operator, limit=limit)
        name = name_splited[0]
        args += [
            ['attribute_value_ids.name', 'ilike', w] for w in name_splited[1:]]
        return super(ProductProduct, self).name_search(
            name, args=args, operator=operator, limit=limit)
