# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    supplier_picking_number = fields.Char(
        string='Supplier Picking Number',
        comodel_name='stock.picking')
