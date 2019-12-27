# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class BookingHolder(models.Model):
    _name = 'booking.holder'
    _description = 'Booking Holder'

    name = fields.Char(
        size=50,
        string='Name',
        required=True,
        copy=False)
    city = fields.Char(
        size=50,
        string='City')
    zip = fields.Char(
        size=50,
        string='Zip')
    country = fields.Char(
        size=50,
        string='Country')
    address = fields.Char(
        size=75,
        string='Address')
    phone1 = fields.Char(
        size=50,
        string='Phone 1')
    phone2 = fields.Char(
        size=50,
        string='Phone 2')
    mobile = fields.Char(
        size=50,
        string='Celular')
    fax = fields.Char(
        size=50,
        string='Fax')
    email = fields.Char(
        size=75,
        string='Email')
    lang = fields.Char(
        size=2,
        string='Language')
    document_type = fields.Char(
        size=75,
        string='Document Type')
    document_number = fields.Char(
        size=200,
        string='Document Number')
    nationality = fields.Char(
        size=75,
        string='Nationality')
