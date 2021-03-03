# -*- coding: utf-8 -*-
###############################################################################
# For copyright and license notices, see __manifest__.py file in root directory
###############################################################################
from openerp import fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    user_id = fields.Many2one(
        domain=[('share', '=', False)],
    )
