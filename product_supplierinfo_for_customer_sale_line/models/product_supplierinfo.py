# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductSupplierinfo(models.Model):
    _inherit = 'product.supplierinfo'

    @api.multi
    def name_get(self):
        if not self.env.context.get('show_customer_info', True):
            return super(ProductSupplierinfo, self).name_get()
        return [
            (ps.id, '%s%s' % (
                ps.product_code and ('[%s] ' % ps.product_code) or '',
                ps.product_name and ps.product_name or ps.product_id.name))
            for ps in self]
