# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, _


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def stock_rotation_button(self):
        ctx = self.env.context.copy()
        ctx.update({'search_default_product_id': self.id})
        return {
            'name': _('Stock Rotation'),
            'view_type': 'form',
            'view_mode': 'graph',
            'res_model': 'stock.rotation.report',
            'type': 'ir.actions.act_window',
            'context': ctx}
