# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    currency_store_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        compute='_get_currency_id',
        store=True)

    @api.one
    @api.depends('currency_id', 'pricelist_id.currency_id')
    def _get_currency_id(self):
        self.currency_store_id = self.currency_id.id
