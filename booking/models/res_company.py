# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class ResCompany(models.Model):
    _inherit = "res.company"

    product_id = fields.Many2one(
        comodel_name='product.template',
        string='Booking Product',
        help="Product for invocing booking")
