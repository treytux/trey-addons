# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    parent_id = fields.Many2one(
        comodel_name='sale.order.line',
        string='Parent product')
