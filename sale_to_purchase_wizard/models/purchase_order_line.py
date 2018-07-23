# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    generate_by_wizard = fields.Boolean(
        string='Generate by wizard: Create purchase from sale order')
