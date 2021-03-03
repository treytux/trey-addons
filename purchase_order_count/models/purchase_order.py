# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchases_count = fields.Integer(
        string='Number of purchases',
        default=1,
    )
