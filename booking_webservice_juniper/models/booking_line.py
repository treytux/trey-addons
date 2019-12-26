# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class BookingLine(models.Model):
    _inherit = 'booking.line'

    juniper_id = fields.Integer(
        string='Juniper Id',
        required=False)
