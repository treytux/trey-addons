# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import fields, models


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    is_ede_danger = fields.Boolean(
        string='EDE Danger',
    )
    ede_invoice_id = fields.Char(
        string='EDE Invoice ID',
    )
