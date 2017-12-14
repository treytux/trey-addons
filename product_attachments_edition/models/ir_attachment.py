# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'
    _order = 'sequence'

    sequence = fields.Integer(
        string='Sequence',
        help="Gives the sequence order when displaying a list of sales order "
             "lines.")
