# -*- coding: utf-8 -*-
# License, author and contributors information in:
# __openerp__.py file at the root folder of this module.
from openerp import models, fields


class BookingWebserviceBuffer(models.Model):
    _inherit = 'booking.webservice.buffer'

    juniper_id = fields.Integer(
        string='Juniper Id',
        required=False)
    juniper_date = fields.Datetime(
        string='Juniper Date',
        help='Create date of the Juniper',
        required=True)
    juniper_last_update = fields.Datetime(
        string='Juniper LastUpdate',
        help='Last Update of the Juniper',
        required=True)
    juniper_end_service = fields.Datetime(
        string='Juniper End Service',
        help='Date End Service of the Juniper',
        required=True)
