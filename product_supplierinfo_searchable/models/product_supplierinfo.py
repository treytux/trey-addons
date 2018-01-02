# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'

    product_id = fields.Many2one(
        comodel_name='product.product',
        string='Variant')

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if len(args) == 1 and args[0][0] == 'supplier_search':
            args = [
                '|',
                ('product_name', args[0][1], args[0][2]),
                ('product_code', args[0][1], args[0][2])]
            if 'type' in self._fields:
                args.append(('type', '=', 'supplier'))
            if 'partner_id' in self.env.context:
                args.append(
                    ('name', '=', self.env.context['partner_id']))
        return super(ProductSupplierInfo, self).search(
            args, offset=offset, limit=limit, order=order, count=count)
