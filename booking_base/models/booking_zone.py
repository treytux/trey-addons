# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class BookingZone(models.Model):
    _name = 'booking.zone'
    _description = 'Booking Zone'

    name = fields.Char(
        string='Name',
        required=True)
    province = fields.Char(
        string='Province')
    country = fields.Char(
        string='Country')
