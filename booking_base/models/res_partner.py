# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    @api.one
    def _booking_count(self):
        self.booking_count = len(self.booking_ids) or 0

    @api.one
    def _booking_line_count(self):
        self.booking_line_count = len(self.booking_line_ids) or 0

    booking_count = fields.Float(
        string="# of Booking",
        compute=_booking_count)
    booking_line_count = fields.Float(
        string="# of Booking Lines",
        compute=_booking_line_count)
    booking_ids = fields.One2many(
        comodel_name='booking',
        inverse_name='agency_id',
        string='Bookings')
    booking_line_ids = fields.One2many(
        comodel_name='booking.line',
        inverse_name='supplier_id',
        string='Booking Lines')
