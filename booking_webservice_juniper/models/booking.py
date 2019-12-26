# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class Booking(models.Model):
    _inherit = 'booking'

    juniper_id = fields.Integer(
        string='Juniper Id',
        required=False)
    juniper_state = fields.Selection(
        string='Juniper State',
        selection=[('Pre', 'on request'),
                   ('Con', 'Confirm'),
                   ('Pag', 'Paid'),
                   ('OK', 'Confirm & Paid'),
                   ('Can', 'Cancel'),
                   ('CaC', 'Cancel by Customer')],
        required=False,
        default='OK')
