# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields


class BookingZone(models.Model):
    _inherit = 'booking.zone'

    methabook_id = fields.Integer(
        string='methabook Id')
    parent_zone_id = fields.Integer(
        string='Parent Zone Id')
