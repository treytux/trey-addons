# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ProductSupplierInfo(models.Model):
    _inherit = 'product.supplierinfo'
    _order = 'date DESC'

    date = fields.Date(
        string='Date',
        default=fields.Date.context_today)
