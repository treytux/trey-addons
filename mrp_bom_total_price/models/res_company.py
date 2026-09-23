# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    mrp_bom_standard_price_digit = fields.Integer(
        string='Mrp Bom Standard Price Decimals',
        required=True,
        default=2,
        help='Decimals in the BOM cost price for comparison with calculated '
             'values',
    )
    mrp_bom_lst_price_digit = fields.Integer(
        string='Mrp Bom List Price Decimals',
        required=True,
        default=2,
        help='Decimals in the BOM list price for comparison with calculated '
             'values',
    )
