# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    seller_id = fields.Many2one(
        compute='_compute_seller_id')

    @api.one
    def _compute_seller_id(self):
        sellers_current_company = self.seller_ids.filtered(
            lambda s: s.name.company_id.id == self.env.user.company_id.id)
        self.seller_id = (
            sellers_current_company and sellers_current_company[0] and
            sellers_current_company[0].name.id or None)
