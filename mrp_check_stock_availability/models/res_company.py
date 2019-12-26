# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    mrp_stock_type = fields.Selection(
        selection=[
            ('virtual', 'Virtual stock'),
            ('real', 'Real stock')],
        string='Mrp stock type',
        default='virtual',
        required=True,
        help="Stock type that will be taken into account when manufacturing "
             "in order to prevent raw materials from being used in excess of "
             "the quantity available.")
