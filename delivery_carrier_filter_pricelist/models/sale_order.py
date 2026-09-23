# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
###############################################################################
from openerp import models, fields


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    carrier_id = fields.Many2one(
        domain=('''[
            '|',
            ('pricelist_id', '=', False),
            ('pricelist_id', '=', pricelist_id)]
            '''),
    )
