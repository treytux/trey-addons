# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @api.model
    def default_get(self, fields):
        res = super(ProductTemplate, self).default_get(fields)
        routes = self.env['stock.location.route'].search([
            ('product_selectable', '=', True),
            ('product_default_route', '=', True)])
        res['route_ids'] = [(6, 0, routes.ids)]
        return res
