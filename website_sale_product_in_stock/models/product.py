# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, api, fields


class ProductProduct(models.Model):
    _inherit = "product.product"

    in_stock = fields.Boolean(
        compute='_compute_in_stock',
        string='In stock',
        readonly=True)

    @api.one
    def _compute_in_stock(self):
        self.in_stock = True and self.sudo().qty_available > 0 or False
