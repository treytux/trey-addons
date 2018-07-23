# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    partner_print_id = fields.Many2one(
        comodel_name='res.partner',
        string='Partner print',
        help='Shipping address will be used to print documents.')

    @api.model
    def create(self, vals):
        res = super(StockPicking, self).create(vals)
        if vals.get('partner_print_id') is False and res.partner_id:
            res.partner_print_id = res.partner_id
        return res
